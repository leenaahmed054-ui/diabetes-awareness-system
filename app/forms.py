import re

from flask_wtf import FlaskForm

from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    SubmitField
)

from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    Optional,
    ValidationError
)


def strong_password(form, field):
    """
    التحقق من قوة كلمة المرور.
    """

    password = field.data or ""

    if len(password) < 10:
        raise ValidationError(
            "Password must contain at least "
            "10 characters."
        )

    if not re.search(r"[A-Z]", password):
        raise ValidationError(
            "Password must contain an "
            "uppercase letter."
        )

    if not re.search(r"[a-z]", password):
        raise ValidationError(
            "Password must contain a "
            "lowercase letter."
        )

    if not re.search(r"[0-9]", password):
        raise ValidationError(
            "Password must contain a number."
        )

    if not re.search(
        r"[^A-Za-z0-9]",
        password
    ):
        raise ValidationError(
            "Password must contain a "
            "special character."
        )


class RegistrationForm(FlaskForm):
    """نموذج إنشاء الحساب."""

    full_name = StringField(
        "Full Name",
        validators=[
            DataRequired(),
            Length(min=2, max=120)
        ]
    )

    email = StringField(
        "Email",
        validators=[
            DataRequired(),
            Email(),
            Length(max=255)
        ]
    )

    phone_number = StringField(
        "WhatsApp Number",
        validators=[
            Optional(),
            Length(min=8, max=20)
        ]
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            strong_password
        ]
    )

    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo(
                "password",
                message="Passwords must match."
            )
        ]
    )

    whatsapp_consent = BooleanField(
        "I agree to receive awareness "
        "messages through WhatsApp."
    )

    submit = SubmitField(
        "Create Account"
    )


class LoginForm(FlaskForm):
    """نموذج تسجيل الدخول."""

    email = StringField(
        "Email",
        validators=[
            DataRequired(),
            Email()
        ]
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired()
        ]
    )

    remember_me = BooleanField(
        "Remember Me"
    )

    submit = SubmitField(
        "Log In"
    )


class LogoutForm(FlaskForm):
    """نموذج تسجيل الخروج المحمي بـCSRF."""

    submit = SubmitField(
        "Log Out"
    )
