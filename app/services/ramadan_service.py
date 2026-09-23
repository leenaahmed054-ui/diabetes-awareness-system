
"""
Ramadan Seasonal Awareness Service.

تحدد هذه الخدمة هل التاريخ داخل فترة رمضان المسجلة
في MySQL، ثم تجهز إشعارًا للمستخدم بعد موافقته.

الخدمة تجهز الإشعار فقط ولا ترسله مباشرة إلى WhatsApp.
الإرسال الفعلي سيضاف لاحقًا عبر WhatsApp Cloud API.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo
import os

from app.extensions import db
from app.models import (
    SeasonalPeriod,
    Notification,
    HealthProfile
)


# استخدام توقيت السعودية بدل الاعتماد على توقيت الخادم.
SAUDI_TIMEZONE = ZoneInfo("Asia/Riyadh")


def ensure_configured_ramadan_period():
    """Create/update the Ramadan period supplied through environment variables."""

    start_value = os.getenv("RAMADAN_START_DATE")
    end_value = os.getenv("RAMADAN_END_DATE")

    if not start_value or not end_value:
        return None

    start_date = normalize_target_date(start_value)
    end_date = normalize_target_date(end_value)

    if end_date < start_date:
        raise ValueError("RAMADAN_END_DATE must be on or after RAMADAN_START_DATE.")

    period_name = os.getenv("RAMADAN_PERIOD_NAME", f"Ramadan {start_date.year}")
    period = SeasonalPeriod.query.filter_by(period_name=period_name).first()

    if period is None:
        period = SeasonalPeriod(period_name=period_name)
        db.session.add(period)

    period.start_date = start_date
    period.end_date = end_date
    period.is_active = True
    db.session.commit()

    return period


def normalize_target_date(target_date=None):
    """
    تحويل القيمة المدخلة إلى تاريخ.

    إذا لم يُرسل تاريخ، نستخدم تاريخ اليوم في السعودية.
    """

    if target_date is None:
        return datetime.now(SAUDI_TIMEZONE).date()

    if isinstance(target_date, datetime):
        return target_date.date()

    if isinstance(target_date, date):
        return target_date

    if isinstance(target_date, str):
        try:
            return datetime.strptime(
                target_date,
                "%Y-%m-%d"
            ).date()

        except ValueError as error:
            raise ValueError(
                "Date must use YYYY-MM-DD format."
            ) from error

    raise TypeError(
        "Target date must be a date, datetime, "
        "YYYY-MM-DD string, or None."
    )


def get_active_ramadan_period(target_date=None):
    """
    البحث عن فترة رمضان الفعالة التي تحتوي التاريخ.

    تواريخ MySQL التي يحددها مدير النظام لها الأولوية
    لأن بداية رمضان قد تعتمد على الإعلان الرسمي.
    """

    checked_date = normalize_target_date(target_date)

    active_period = (
        SeasonalPeriod.query
        .filter(
            SeasonalPeriod.is_active.is_(True),
            SeasonalPeriod.start_date <= checked_date,
            SeasonalPeriod.end_date >= checked_date,
            SeasonalPeriod.period_name.ilike("%ramadan%")
        )
        .order_by(SeasonalPeriod.start_date.desc())
        .first()
    )

    return active_period


def create_ramadan_message(pregnancy_status=None):
    """
    إنشاء رسالة توعوية عامة لشهر رمضان.

    لا تتضمن الرسالة تشخيصًا أو تعديل جرعة دواء.
    """

    message_parts = [
        (
            "Ramadan health awareness: keep meals balanced, "
            "maintain hydration during non-fasting hours, and "
            "follow the health plan provided by your qualified "
            "healthcare professional."
        ),
        (
            "If you have diabetes, unusual glucose readings, "
            "or use medication, seek medical guidance about "
            "fasting and monitoring."
        )
    ]

    # إضافة تنبيه منفصل للمرأة الحامل.
    if pregnancy_status == "pregnant":
        message_parts.append(
            "Pregnancy requires individual medical assessment. "
            "Please consult your obstetric or healthcare "
            "professional before fasting."
        )

    message_parts.append(
        "This message is for awareness only and is not "
        "a diagnosis or treatment recommendation."
    )

    return " ".join(message_parts)


def prepare_ramadan_notification(
    user,
    assessment_id=None,
    target_date=None
):
    """
    تجهيز إشعار رمضان في MySQL.

    النتائج الممكنة:
    - no_active_ramadan
    - consent_required
    - phone_required
    - duplicate
    - prepared

    لا تنفذ هذه الدالة commit حتى يتحكم المسار أو
    المجدول في المعاملة كاملة.
    """

    if user is None or user.id is None:
        raise ValueError(
            "A saved user is required."
        )

    checked_date = normalize_target_date(target_date)

    # التأكد أن التاريخ داخل رمضان المسجل في MySQL.
    active_period = get_active_ramadan_period(
        checked_date
    )

    if active_period is None:
        return {
            "status": "no_active_ramadan",
            "target_date": checked_date.isoformat(),
            "notification": None
        }

    # احترام موافقة المستخدم قبل تجهيز رسالة واتساب.
    if not user.whatsapp_consent:
        return {
            "status": "consent_required",
            "target_date": checked_date.isoformat(),
            "period_id": active_period.id,
            "notification": None
        }

    # التأكد من وجود رقم هاتف مشفر.
    if not user.phone_number_encrypted:
        return {
            "status": "phone_required",
            "target_date": checked_date.isoformat(),
            "period_id": active_period.id,
            "notification": None
        }

    # إدخال رقم الفترة في النوع يمنع إرسال أكثر من
    # إشعار رمضان للمستخدم خلال الفترة نفسها.
    notification_type = (
        f"ramadan_awareness_{active_period.id}"
    )

    # البحث عن إشعار سابق للمستخدم والفترة نفسها.
    existing_notification = Notification.query.filter_by(
        user_id=user.id,
        notification_type=notification_type
    ).first()

    if existing_notification is not None:
        return {
            "status": "duplicate",
            "target_date": checked_date.isoformat(),
            "period_id": active_period.id,
            "notification_id": existing_notification.id,
            "notification": existing_notification
        }

    # قراءة حالة الحمل من الملف الصحي إن وُجد.
    health_profile = HealthProfile.query.filter_by(
        user_id=user.id
    ).first()

    pregnancy_status = (
        health_profile.pregnancy_status
        if health_profile is not None
        else None
    )

    # إنشاء نص الإشعار.
    message_text = create_ramadan_message(
        pregnancy_status=pregnancy_status
    )

    # إنشاء سجل انتظار داخل MySQL.
    notification = Notification(
        user_id=user.id,
        assessment_id=assessment_id,
        notification_type=notification_type,
        message_text=message_text,
        delivery_status="pending"
    )

    db.session.add(notification)

    # flush يطلب رقم الإشعار من MySQL دون تنفيذ commit.
    db.session.flush()

    return {
        "status": "prepared",
        "target_date": checked_date.isoformat(),
        "period_id": active_period.id,
        "period_name": active_period.period_name,
        "notification_id": notification.id,
        "notification": notification
    }
