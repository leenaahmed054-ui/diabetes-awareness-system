
"""
WhatsApp Notification Dispatcher.

يقرأ الإشعارات pending من MySQL، ثم:
1. يتحقق من موافقة المستخدم.
2. يفك تشفير رقم الهاتف داخل الذاكرة فقط.
3. يحدد WhatsApp Template المناسب.
4. يرسل الرسالة أو يحاكيها في DRY_RUN.
5. يحدث حالة الإشعار عند الإرسال الحقيقي.
"""

import os
from datetime import datetime, timezone

from app.extensions import db

from app.models import (
    User,
    Assessment,
    Notification
)

from app.services.security_service import decrypt_text

from app.services.whatsapp_service import (
    is_dry_run_enabled,
    send_template_message,
    WhatsAppConfigurationError,
    WhatsAppDeliveryError
)
from app.services.daily_tip_service import (
    DAILY_TIP_PREFIX,
    daily_tip_type,
    daily_tips_enabled,
)
from app.services.ramadan_service import (
    get_active_ramadan_period,
    normalize_target_date,
)

def get_template_information(notification):
    """
    تحديد اسم القالب والمتغيرات بناءً على نوع الإشعار.

    أسماء القوالب تُقرأ من Environment Variables
    حتى نستطيع تغييرها دون تعديل الكود.
    """

    notification_type = notification.notification_type
    if notification_type.startswith(DAILY_TIP_PREFIX):
        return {
            "template_name": os.getenv(
                "WHATSAPP_DAILY_TIP_TEMPLATE_NAME", "diabetes_daily_tip"
            ),
            "language_code": os.getenv(
                "WHATSAPP_DAILY_TIP_TEMPLATE_LANGUAGE", "ar"
            ),
            "body_parameters": [notification.message_text],
        }
    # إشعارات رمضان.
    if notification_type.startswith(
        "ramadan_awareness_"
    ):
        template_name = os.getenv(
            "WHATSAPP_RAMADAN_TEMPLATE_NAME",
            "ramadan_awareness"
        )

        body_parameters = [
            notification.message_text
        ]

        return {
            "template_name": template_name,
            "language_code": os.getenv(
                "WHATSAPP_TEMPLATE_LANGUAGE",
                "en"
            ),
            "body_parameters": body_parameters
        }

    # إشعارات نتيجة التقييم.
    if notification_type == "assessment_result":

        if notification.assessment_id is None:
            raise ValueError(
                "Assessment notification requires assessment_id."
            )

        assessment = db.session.get(
            Assessment,
            notification.assessment_id
        )

        if assessment is None:
            raise ValueError(
                "The related assessment was not found."
            )

        template_name = os.getenv(
            "WHATSAPP_ASSESSMENT_TEMPLATE_NAME",
            "diabetes_assessment_result"
        )

        # القالب المتوقع يحتوي متغيرين:
        # 1. النسبة المئوية.
        # 2. مستوى الخطر.
        body_parameters = [
            f"{assessment.model_risk_score * 100:.2f}%",
            assessment.risk_level
        ]

        return {
            "template_name": template_name,
            "language_code": os.getenv(
                "WHATSAPP_TEMPLATE_LANGUAGE",
                "en"
            ),
            "body_parameters": body_parameters
        }

    raise ValueError(
        "Unsupported notification type."
    )


def dispatch_pending_notifications(limit=100, notification_ids=None):
    """
    معالجة دفعة من الإشعارات المعلقة.

    في DRY_RUN:
    - لا يحدث اتصال حقيقي مع Meta.
    - تبقى حالة الإشعار pending.
    - لا يُحفظ رقم الهاتف بعد فك التشفير.

    في الإنتاج:
    - sent عند قبول Meta للطلب.
    - failed عند حدوث خطأ.
    """

    if not isinstance(limit, int) or limit <= 0:
        raise ValueError(
            "limit must be a positive integer."
        )

    # إنشاء الاستعلام الأساسي للإشعارات المعلقة.
    pending_query = Notification.query.filter_by(
        delivery_status="pending"
    )

    # عند إرسال notification_ids نعالج هذه الإشعارات فقط.
    # يُستخدم ذلك في الاختبارات والمهام الإدارية المحددة.
    if notification_ids is not None:

        if not isinstance(
            notification_ids,
            (list, tuple, set)
        ):
            raise TypeError(
                "notification_ids must be a list, tuple, or set."
            )

        # تحويل القيم إلى أرقام صحيحة وإزالة التكرار.
        safe_notification_ids = sorted({
            int(notification_id)
            for notification_id in notification_ids
        })

        # إذا كانت القائمة فارغة فلا نعالج أي إشعار.
        
        if not safe_notification_ids:
            return {
                "mode": (
                    "dry_run"
                    if is_dry_run_enabled()
                    else "production"
                ),
                "found": 0,
                "submitted": 0,
                "dry_run": 0,
                "failed": 0,
                "skipped": 0,
                "results": []
            }

        pending_query = pending_query.filter(
            Notification.id.in_(
                safe_notification_ids
            )
        )

    # قراءة عدد محدود لمنع تحميل جميع الإشعارات.
    pending_notifications = (
        pending_query
        .order_by(Notification.created_at.asc())
        .limit(limit)
        .all()
    )

    dispatch_report = {
        "mode": (
            "dry_run"
            if is_dry_run_enabled()
            else "production"
        ),
        "found": len(pending_notifications),
        "submitted": 0,
        "dry_run": 0,
        "failed": 0,
        "skipped": 0,
        "results": []
    }

    for notification in pending_notifications:

        try:
                                 
                                               if notification.notification_type.startswith(DAILY_TIP_PREFIX):
                day = normalize_target_date(None)
                if notification.notification_type != daily_tip_type(day):
                    notification.delivery_status = "expired"
                    db.session.commit()
                    reason = "expired"
                elif not daily_tips_enabled() or get_active_ramadan_period(day) is not None:
                    reason = "daily_tip_inactive"
                else:
                    reason = None

                if reason:
                    dispatch_report["skipped"] += 1
                    dispatch_report["results"].append({
                        "notification_id": notification.id,
                        "status": reason,
                    })
                    continue
            # قراءة صاحب الإشعار.
            user = db.session.get(
                User,
                notification.user_id
            )

            if user is None:
                raise ValueError(
                    "Notification user was not found."
                )

            # عدم إرسال رسائل للحساب غير الفعال.
            if not user.is_active_account:
                dispatch_report["skipped"] += 1

                dispatch_report["results"].append({
                    "notification_id": notification.id,
                    "status": "inactive_account"
                })

                continue

            # التحقق من الموافقة في لحظة الإرسال.
            if not user.whatsapp_consent:
                dispatch_report["skipped"] += 1

                dispatch_report["results"].append({
                    "notification_id": notification.id,
                    "status": "consent_missing"
                })

                continue

            if not user.phone_number_encrypted:
                raise ValueError(
                    "Encrypted phone number is missing."
                )

            # فك الرقم داخل الذاكرة فقط.
            # لا نطبعه ولا نخزنه كنص صريح.
            decrypted_phone = decrypt_text(
                user.phone_number_encrypted
            )

            # تحديد القالب والمتغيرات.
            template_information = (
                get_template_information(notification)
            )

            # إرسال الرسالة أو تنفيذ DRY_RUN.
            send_result = send_template_message(
                phone_number=decrypted_phone,
                template_name=template_information[
                    "template_name"
                ],
                language_code=template_information[
                    "language_code"
                ],
                body_parameters=template_information[
                    "body_parameters"
                ]
            )

            if send_result["status"] == "dry_run":
                # نبقيها pending حتى يمكن إرسالها لاحقًا
                # عند تفعيل وضع الإنتاج.
                dispatch_report["dry_run"] += 1

                dispatch_report["results"].append({
                    "notification_id": notification.id,
                    "status": "dry_run"
                })

            elif send_result["status"] == "submitted":
                # Meta قبلت طلب الرسالة.
                notification.delivery_status = "submitted"
                notification.external_message_id = (
                    send_result["external_message_id"]
                )
                notification.sent_at = datetime.now(
                    timezone.utc
                )
                notification.error_message = None

                db.session.commit()

                dispatch_report["submitted"] += 1

                dispatch_report["results"].append({
                    "notification_id": notification.id,
                    "status": "sent",
                    "external_message_id": (
                        send_result["external_message_id"]
                    )
                })

            # حذف الرقم المفكوك من المتغير بعد استخدامه.
            decrypted_phone = None

        except (
            ValueError,
            TypeError,
            WhatsAppConfigurationError,
            WhatsAppDeliveryError
        ) as error:
            db.session.rollback()

            dispatch_report["failed"] += 1

            # إعادة قراءة الإشعار بعد rollback.
            failed_notification = db.session.get(
                Notification,
                notification.id
            )

            # في DRY_RUN لا نحول الخطأ إلى failed دائمًا؛
            # أما أخطاء البيانات فنحتاج تسجيلها.
            if failed_notification is not None:
                failed_notification.delivery_status = "failed"

                # نخزن نوع الخطأ ورسالة مختصرة دون أسرار.
                failed_notification.error_message = (
                    f"{type(error).__name__}: {str(error)}"
                )[:1000]

                db.session.commit()

            dispatch_report["results"].append({
                "notification_id": notification.id,
                "status": "failed",
                "error_type": type(error).__name__
            })

        except Exception as error:
            # التقاط أي خطأ غير متوقع دون إيقاف الدفعة.
            db.session.rollback()

            dispatch_report["failed"] += 1

            failed_notification = db.session.get(
                Notification,
                notification.id
            )

            if failed_notification is not None:
                failed_notification.delivery_status = "failed"

                # لا نخزن تفاصيل داخلية قد تكون حساسة.
                failed_notification.error_message = (
                    f"Unexpected {type(error).__name__}"
                )

                db.session.commit()

            dispatch_report["results"].append({
                "notification_id": notification.id,
                "status": "failed",
                "error_type": type(error).__name__
            })

    return dispatch_report
