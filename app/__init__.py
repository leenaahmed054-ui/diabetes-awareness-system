import os
from pathlib import Path

from flask import Flask, jsonify, redirect, url_for
from dotenv import load_dotenv
from flask_login import current_user
from werkzeug.middleware.proxy_fix import ProxyFix

from .extensions import (
    db,
    login_manager,
    csrf
)


def create_app(test_config=None):
    """
    إنشاء تطبيق Flask وربط قاعدة البيانات
    والحماية وRoutes.
    """

    web_app_root = (
        Path(__file__)
        .resolve()
        .parent
        .parent
    )

    # تحميل الأسرار إن وجد ملف .env.
    load_dotenv(
        web_app_root / ".env"
    )

    from config import Config

    app = Flask(__name__)
    app.config.from_object(Config)

    # الاستضافة تنهي HTTPS عند الـ proxy؛ هذا يجعل Flask يحترم
    # البروتوكول واسم المضيف الأصليين.
    app.wsgi_app = ProxyFix(
        app.wsgi_app,
        x_for=1,
        x_proto=1,
        x_host=1
    )

    # السماح بإعدادات اختبار مؤقتة.
    if test_config:
        app.config.update(test_config)

    if not app.config.get("SECRET_KEY"):
        raise RuntimeError(
            "SECRET_KEY is not configured."
        )

    if not app.config.get(
        "SQLALCHEMY_DATABASE_URI"
    ):
        raise RuntimeError(
            "DATABASE_URL is not configured."
        )

    # ربط الإضافات.
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # إعداد Flask-Login.
    login_manager.login_view = "auth.login"
    login_manager.login_message = (
        "Please log in to access this page."
    )
    login_manager.login_message_category = "error"
    login_manager.session_protection = "strong"

    @login_manager.user_loader
    def load_user(user_id):

        from .models import User

        try:
            numeric_user_id = int(user_id)

        except (ValueError, TypeError):
            return None

        return db.session.get(
            User,
            numeric_user_id
        )

    # تسجيل Auth Blueprint.
    from .routes.auth import (
        auth_blueprint
    )

    app.register_blueprint(
        auth_blueprint
    )

    @app.get("/")
    def index():
        """فتح الصفحة المناسبة للزائر أو المستخدم المسجل."""

        if current_user.is_authenticated:
            return redirect(url_for("auth.dashboard"))

        return redirect(url_for("auth.login"))

    # فحص Backend.
    @app.get("/health")
    def health_check():

        return jsonify({
            "status": "healthy",
            "service": (
                "Diabetes Risk Awareness System"
            )
        }), 200


    # استيراد مسارات التقييم بعد تهيئة إضافات Flask.
    # هذا يساعد أيضًا على تجنب Circular Import.
    from app.routes.assessment import assessment_bp

    # تسجيل روابط:
    # /assessment/new
    # /assessment/history
    # /assessment/<assessment_id>
    app.register_blueprint(assessment_bp)

    from app.routes.tasks import tasks_bp
    app.register_blueprint(tasks_bp)


    # تسجيل أوامر تجهيز رمضان وإرسال WhatsApp.
    from app.commands import register_commands
    register_commands(app)

    # إنشاء الجداول الناقصة عند أول نشر، دون حذف البيانات الموجودة.
    if os.getenv("AUTO_CREATE_TABLES", "true").lower() == "true":
        with app.app_context():
            db.create_all()
            from app.services.ramadan_service import ensure_configured_ramadan_period
            ensure_configured_ramadan_period()

    return app
