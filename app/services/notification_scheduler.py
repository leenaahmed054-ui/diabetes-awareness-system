
"""
Daily Notification Scheduler.

هذه الخدمة تبحث عن المستخدمين الذين:
1. حسابهم فعال.
2. وافقوا على رسائل WhatsApp.
3. لديهم رقم هاتف مشفر.
4. التاريخ الحالي يقع داخل فترة رمضان الفعالة.

ثم تجهز إشعارًا واحدًا فقط لكل مستخدم خلال الفترة.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from app.extensions import db
from app.models import User

from app.services.ramadan_service import (
    normalize_target_date,
    get_active_ramadan_period,
    prepare_ramadan_notification
)


SAUDI_TIMEZONE = ZoneInfo("Asia/Riyadh")


def prepare_daily_ramadan_notifications(
    target_date=None,
    batch_size=100
):
    """
    تجهيز إشعارات رمضان للمستخدمين المؤهلين.

    batch_size يمنع تحميل جميع المستخدمين إلى الذاكرة
    دفعة واحدة، وهذا أنسب عند زيادة حجم قاعدة البيانات.
    """

    checked_date = normalize_target_date(target_date)

    # التأكد من صحة حجم الدفعة.
    if not isinstance(batch_size, int) or batch_size <= 0:
        raise ValueError(
            "batch_size must be a positive integer."
        )

    # البحث عن فترة رمضان الفعالة.
    active_period = get_active_ramadan_period(
        checked_date
    )

    # إعداد تقرير تشغيل يساعد في التوثيق والمراقبة.
    run_report = {
        "run_time_saudi": datetime.now(
            SAUDI_TIMEZONE
        ).isoformat(),
        "target_date": checked_date.isoformat(),
        "period_id": None,
        "period_name": None,
        "eligible_users": 0,
        "prepared": 0,
        "duplicate": 0,
        "failed": 0,
        "errors": []
    }

    # إذا لم نكن داخل رمضان لا نجهز أي إشعار.
    if active_period is None:
        run_report["status"] = "no_active_ramadan"
        return run_report

    run_report["period_id"] = active_period.id
    run_report["period_name"] = active_period.period_name
    run_report["status"] = "completed"

    # سنستخدم رقم المستخدم لتقسيم القراءة إلى دفعات.
    last_user_id = 0

    while True:
        # اختيار المستخدمين المؤهلين فقط.
        users_batch = (
            User.query
            .filter(
                User.id > last_user_id,
                User.is_active_account.is_(True),
                User.whatsapp_consent.is_(True),
                User.phone_number_encrypted.isnot(None)
            )
            .order_by(User.id.asc())
            .limit(batch_size)
            .all()
        )

        # عند عدم وجود مستخدمين آخرين تنتهي الحلقة.
        if not users_batch:
            break

        for user in users_batch:
            # حفظ آخر ID للانتقال إلى الدفعة التالية.
            last_user_id = user.id

            run_report["eligible_users"] += 1

            try:
                # تجهيز الإشعار دون إرساله إلى WhatsApp.
                result = prepare_ramadan_notification(
                    user=user,
                    target_date=checked_date
                )

                if result["status"] == "prepared":
                    # حفظ إشعار المستخدم في MySQL.
                    db.session.commit()
                    run_report["prepared"] += 1

                elif result["status"] == "duplicate":
                    # لا ننشئ نسخة أخرى من الإشعار.
                    db.session.rollback()
                    run_report["duplicate"] += 1

                else:
                    # الحالات الأخرى غير متوقعة هنا لأن الاستعلام
                    # اختار المستخدمين الذين لديهم موافقة ورقم.
                    db.session.rollback()

                    run_report["failed"] += 1
                    run_report["errors"].append({
                        "user_id": user.id,
                        "status": result["status"]
                    })

            except Exception as error:
                # فشل مستخدم واحد لا يوقف باقي المستخدمين.
                db.session.rollback()

                run_report["failed"] += 1
                run_report["errors"].append({
                    "user_id": user.id,
                    "error_type": type(error).__name__
                })

    return run_report
