from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from .extensions import db


def utc_now():
    """إرجاع الوقت الحالي بتوقيت UTC."""
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    """جدول حسابات المستخدمين."""

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    full_name = db.Column(
        db.String(120),
        nullable=False
    )

    email = db.Column(
        db.String(255),
        unique=True,
        nullable=False,
        index=True
    )

    # لا يتم حفظ كلمة المرور الأصلية.
    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    # يُحفظ رقم واتساب مشفرًا.
    phone_number_encrypted = db.Column(
        db.LargeBinary,
        nullable=True
    )

    whatsapp_consent = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    whatsapp_consent_at = db.Column(
        db.DateTime,
        nullable=True
    )

    is_active_account = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=utc_now
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now
    )

    # حذف البيانات التابعة عند حذف الحساب.
    health_profile = db.relationship(
        "HealthProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    assessments = db.relationship(
        "Assessment",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    notifications = db.relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def set_password(self, password):
        """تحويل كلمة المرور إلى Hash."""
        self.password_hash = (
            generate_password_hash(password)
        )

    def check_password(self, password):
        """التحقق من كلمة المرور."""
        return check_password_hash(
            self.password_hash,
            password
        )

    @property
    def is_active(self):
        """مطلوبة من Flask-Login."""
        return self.is_active_account


class HealthProfile(db.Model):
    """الملف الصحي الحالي للمستخدم."""

    __tablename__ = "health_profiles"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        unique=True,
        nullable=False,
        index=True
    )

    gender = db.Column(
        db.String(10),
        nullable=False
    )

    pregnancy_status = db.Column(
        db.String(30),
        nullable=True
    )

    parity = db.Column(
        db.Integer,
        nullable=True
    )

    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now
    )

    user = db.relationship(
        "User",
        back_populates="health_profile"
    )


class Assessment(db.Model):
    """سجل كل تقييم صحي أجراه المستخدم."""

    __tablename__ = "assessments"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    # نحفظ العمر وقت إجراء التقييم.
    age = db.Column(
        db.Integer,
        nullable=False
    )

    gender_code = db.Column(
        db.Integer,
        nullable=False
    )

    bmi = db.Column(
        db.Numeric(6, 2),
        nullable=False
    )

    systolic_bp = db.Column(
        db.Numeric(6, 2),
        nullable=False
    )

    diastolic_bp = db.Column(
        db.Numeric(6, 2),
        nullable=False
    )

    glucose = db.Column(
        db.Numeric(7, 2),
        nullable=False
    )

    physically_active = db.Column(
        db.Boolean,
        nullable=False
    )

    pregnancy_status = db.Column(
        db.String(30),
        nullable=True
    )

    parity = db.Column(
        db.Integer,
        nullable=True
    )

    # درجة النموذج بين 0 و1.
    model_risk_score = db.Column(
        db.Numeric(7, 6),
        nullable=False
    )

    risk_level = db.Column(
        db.String(20),
        nullable=False
    )

    predicted_class = db.Column(
        db.Integer,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=utc_now,
        index=True
    )

    user = db.relationship(
        "User",
        back_populates="assessments"
    )


class Notification(db.Model):
    """سجل إشعارات واتساب والتنبيهات."""

    __tablename__ = "notifications"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "users.id",
            ondelete="CASCADE"
        ),
        nullable=False,
        index=True
    )

    assessment_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "assessments.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    notification_type = db.Column(
        db.String(50),
        nullable=False,
        index=True
    )

    message_text = db.Column(
        db.Text,
        nullable=False
    )

    delivery_status = db.Column(
        db.String(30),
        nullable=False,
        default="Pending"
    )

    external_message_id = db.Column(
        db.String(255),
        nullable=True
    )

    error_message = db.Column(
        db.Text,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=utc_now
    )

    sent_at = db.Column(
        db.DateTime,
        nullable=True
    )

    user = db.relationship(
        "User",
        back_populates="notifications"
    )

    # منع تكرار نفس نوع الرسالة للمستخدم
    # في التاريخ المسجل لاحقًا سيكون عبر منطق الخدمة.


class SeasonalPeriod(db.Model):
    """فترات موسمية مثل رمضان."""

    __tablename__ = "seasonal_periods"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    period_name = db.Column(
        db.String(50),
        nullable=False,
        index=True
    )

    start_date = db.Column(
        db.Date,
        nullable=False
    )

    end_date = db.Column(
        db.Date,
        nullable=False
    )

    is_active = db.Column(
        db.Boolean,
        nullable=False,
        default=True
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=utc_now
    )
