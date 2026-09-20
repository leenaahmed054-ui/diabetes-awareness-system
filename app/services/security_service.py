import os

from cryptography.fernet import (
    Fernet,
    InvalidToken
)


def get_encryption_cipher():
    """
    تنشئ أداة التشفير باستخدام المفتاح
    المحفوظ في Environment Variable.
    """

    encryption_key = os.getenv(
        "DATA_ENCRYPTION_KEY"
    )

    if not encryption_key:
        raise RuntimeError(
            "DATA_ENCRYPTION_KEY is not configured."
        )

    return Fernet(
        encryption_key.encode("utf-8")
    )


def encrypt_text(plain_text):
    """
    تشفر نصًا قبل حفظه في قاعدة البيانات.
    """

    if plain_text is None:
        return None

    cleaned_text = str(plain_text).strip()

    if not cleaned_text:
        return None

    cipher = get_encryption_cipher()

    return cipher.encrypt(
        cleaned_text.encode("utf-8")
    )


def decrypt_text(encrypted_value):
    """
    تفك تشفير النص عند الحاجة المصرح بها.
    """

    if encrypted_value is None:
        return None

    cipher = get_encryption_cipher()

    try:
        decrypted_value = cipher.decrypt(
            encrypted_value
        )

    except InvalidToken as error:
        raise ValueError(
            "The encrypted value could not "
            "be decrypted."
        ) from error

    return decrypted_value.decode("utf-8")
