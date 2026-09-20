
"""
Official WhatsApp Cloud API Service.

الأسرار لا تحفظ داخل هذا الملف.
تُقرأ من Environment Variables فقط.

الوضع الافتراضي DRY_RUN=True، ولذلك لن تُرسل
أي رسالة حقيقية أثناء تطوير المشروع.
"""

import os
import re

import requests


class WhatsAppConfigurationError(Exception):
    """
    خطأ خاص بنقص إعدادات WhatsApp.
    """


class WhatsAppDeliveryError(Exception):
    """
    خطأ خاص بفشل طلب الإرسال إلى Meta.
    """


def is_dry_run_enabled():
    """
    قراءة وضع الاختبار من متغيرات البيئة.

    القيمة الافتراضية true لحماية المشروع من
    الإرسال غير المقصود أثناء التطوير.
    """

    dry_run_value = os.getenv(
        "WHATSAPP_DRY_RUN",
        "true"
    )

    return dry_run_value.strip().lower() in {
        "1",
        "true",
        "yes",
        "on"
    }


def normalize_whatsapp_number(phone_number):
    """
    تجهيز رقم الهاتف بصيغة أرقام دولية فقط.

    مثال:
    +966 50 123 4567
    يصبح:
    966501234567
    """

    if phone_number is None:
        raise ValueError(
            "A WhatsApp phone number is required."
        )

    normalized_number = re.sub(
        r"[^0-9]",
        "",
        str(phone_number)
    )

    # فحص عام لطول الرقم الدولي.
    if not 8 <= len(normalized_number) <= 15:
        raise ValueError(
            "The WhatsApp number must use a valid "
            "international format."
        )

    return normalized_number


def get_whatsapp_configuration():
    """
    قراءة إعدادات Meta من Environment Variables.

    لا نطبع Access Token في أي نتيجة أو Log.
    """

    configuration = {
        "access_token": os.getenv(
            "WHATSAPP_ACCESS_TOKEN"
        ),
        "phone_number_id": os.getenv(
            "WHATSAPP_PHONE_NUMBER_ID"
        ),
        "graph_api_version": os.getenv(
            "WHATSAPP_GRAPH_API_VERSION"
        )
    }

    missing_settings = [
        setting_name
        for setting_name, setting_value
        in configuration.items()
        if not setting_value
    ]

    if missing_settings:
        raise WhatsAppConfigurationError(
            "Missing WhatsApp environment settings: "
            + ", ".join(missing_settings)
        )

    return configuration


def create_template_payload(
    phone_number,
    template_name,
    language_code="en",
    body_parameters=None
):
    """
    إنشاء JSON لرسالة Template معتمدة من Meta.

    body_parameters تمثل القيم المتغيرة داخل القالب،
    مثل مستوى الخطر أو الرسالة المختصرة.
    """

    normalized_number = normalize_whatsapp_number(
        phone_number
    )

    if not template_name:
        raise ValueError(
            "An approved WhatsApp template name is required."
        )

    if body_parameters is None:
        body_parameters = []

    # تحويل المتغيرات إلى صيغة Meta المطلوبة.
    formatted_parameters = [
        {
            "type": "text",
            "text": str(parameter)
        }
        for parameter in body_parameters
    ]

    template_data = {
        "name": template_name,
        "language": {
            "code": language_code
        }
    }

    # لا نضيف components إذا لم يحتوِ القالب على متغيرات.
    if formatted_parameters:
        template_data["components"] = [
            {
                "type": "body",
                "parameters": formatted_parameters
            }
        ]

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": normalized_number,
        "type": "template",
        "template": template_data
    }

    return payload


def send_template_message(
    phone_number,
    template_name,
    language_code="en",
    body_parameters=None
):
    """
    إرسال WhatsApp Template أو محاكاة الإرسال.

    في DRY_RUN:
    - لا يُقرأ Access Token.
    - لا يحدث اتصال مع Meta.
    - يُرجع Payload للاختبار فقط.

    في وضع الإنتاج:
    - تُقرأ الأسرار من Environment Variables.
    - يُرسل HTTPS POST إلى Graph API.
    """

    payload = create_template_payload(
        phone_number=phone_number,
        template_name=template_name,
        language_code=language_code,
        body_parameters=body_parameters
    )

    # الوضع الآمن الافتراضي.
    if is_dry_run_enabled():
        return {
            "status": "dry_run",
            "sent": False,
            "payload": payload,
            "external_message_id": None
        }

    # قراءة الإعدادات فقط عند الإرسال الحقيقي.
    configuration = get_whatsapp_configuration()

    api_url = (
        "https://graph.facebook.com/"
        f"{configuration['graph_api_version']}/"
        f"{configuration['phone_number_id']}/messages"
    )

    headers = {
        "Authorization": (
            f"Bearer {configuration['access_token']}"
        ),
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=20
        )

    except requests.RequestException as error:
        raise WhatsAppDeliveryError(
            "Could not connect to WhatsApp Cloud API."
        ) from error

    # محاولة قراءة استجابة Meta بصيغة JSON.
    try:
        response_data = response.json()

    except ValueError:
        response_data = {}

    if not response.ok:
        # لا نعيد Access Token أو كامل البيانات الحساسة.
        meta_error = response_data.get(
            "error",
            {}
        )

        safe_error_message = meta_error.get(
            "message",
            "WhatsApp Cloud API rejected the request."
        )

        raise WhatsAppDeliveryError(
            safe_error_message
        )

    # استخراج Message ID لحفظه في MySQL.
    messages = response_data.get("messages", [])

    external_message_id = (
        messages[0].get("id")
        if messages
        else None
    )

    return {
        "status": "submitted",
        "sent": True,
        "payload": payload,
        "external_message_id": external_message_id
    }
