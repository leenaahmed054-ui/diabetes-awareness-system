import os
from datetime import timedelta


def database_url():
    """Return a SQLAlchemy-compatible database URL."""

    value = os.getenv("DATABASE_URL")

    if value and value.startswith("postgres://"):
        return value.replace("postgres://", "postgresql+psycopg://", 1)

    if value and value.startswith("postgresql://"):
        return value.replace("postgresql://", "postgresql+psycopg://", 1)

    return value


class Config:
    """الإعدادات المشتركة والآمنة للتطبيق."""

    # يُقرأ المفتاح من Environment Variable.
    # لا نحفظ المفتاح الحقيقي داخل GitHub.
    SECRET_KEY = os.getenv("SECRET_KEY")

    # يعمل مع PostgreSQL في الاستضافة، ومع MySQL محليًا عند الحاجة.
    SQLALCHEMY_DATABASE_URI = database_url()

    # تعطيل تتبع غير ضروري يستهلك الذاكرة.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # التأكد من أن الاتصال بقاعدة البيانات
    # ما زال صالحًا قبل استخدامه.
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280
    }

    # إعدادات Session Cookie.
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # في الاستضافة باستخدام HTTPS ستكون True.
    # أثناء الاختبار المحلي يمكن ضبطها False.
    SESSION_COOKIE_SECURE = (
        os.getenv(
            "COOKIE_SECURE",
            "false"
        ).lower() == "true"
    )

    # إعدادات Remember Me Cookie.
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"

    REMEMBER_COOKIE_SECURE = (
        os.getenv(
            "COOKIE_SECURE",
            "false"
        ).lower() == "true"
    )

    # مدة حفظ تسجيل الدخول.
    REMEMBER_COOKIE_DURATION = timedelta(
        days=14
    )

    # مدة جلسة الاستخدام العادية.
    PERMANENT_SESSION_LIFETIME = timedelta(
        hours=2
    )

    # حماية نماذج Flask-WTF.
    WTF_CSRF_ENABLED = True

    # الحد الأقصى للطلب: 2 MB.
    MAX_CONTENT_LENGTH = (
        2 * 1024 * 1024
    )
