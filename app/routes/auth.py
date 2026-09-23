import re
from datetime import timedelta

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    session,
    url_for
)

from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user
)

from sqlalchemy import select

from ..extensions import db

from ..forms import (
    RegistrationForm,
    LoginForm,
    LogoutForm
)

from ..models import (
    User,
    utc_now
)

from ..services.security_service import (
    encrypt_text
)


auth_blueprint = Blueprint(
    "auth",
    __name__,
    url_prefix="/auth"
)


def normalize_phone_number(phone_number):
    """
    تنظف رقم الهاتف دون تخزينه كنص مفتوح.
    """

    if not phone_number:
        return None

    cleaned_phone = (
        str(phone_number)
        .replace(" ", "")
        .replace("-", "")
        .strip()
    )

    # قبول علامة + اختيارية ثم 8 إلى 15 رقمًا.
    if not re.fullmatch(
        r"\+?[0-9]{8,15}",
        cleaned_phone
    ):
        raise ValueError(
            "Enter a valid international "
            "phone number."
        )

    return cleaned_phone


@auth_blueprint.route(
    "/register",
    methods=["GET", "POST"]
)
def register():
    """إنشاء حساب مستخدم جديد."""

    if current_user.is_authenticated:
        return redirect(
            url_for("auth.dashboard")
        )

    form = RegistrationForm()

    if form.validate_on_submit():

        normalized_email = (
            form.email.data
            .strip()
            .lower()
        )

        # التحقق من عدم تكرار البريد.
        existing_user = db.session.scalar(
            select(User).where(
                User.email == normalized_email
            )
        )

        if existing_user:
            flash(
                "Unable to create an account "
                "with the supplied information.",
                "error"
            )

            return render_template(
                "register.html",
                form=form
            )

        try:
            phone_number = (
                normalize_phone_number(
                    form.phone_number.data
                )
            )

        except ValueError as error:
            flash(str(error), "error")

            return render_template(
                "register.html",
                form=form
            )

        # لا يمكن الموافقة على واتساب دون رقم.
        if (
            form.whatsapp_consent.data
            and not phone_number
        ):
            flash(
                "A WhatsApp number is required "
                "when consent is selected.",
                "error"
            )

            return render_template(
                "register.html",
                form=form
            )

        user = User(
            full_name=(
                form.full_name.data.strip()
            ),
            email=normalized_email,
            phone_number_encrypted=(
                encrypt_text(phone_number)
                if phone_number
                else None
            ),
            whatsapp_consent=(
                form.whatsapp_consent.data
            ),
            whatsapp_consent_at=(
                utc_now()
                if form.whatsapp_consent.data
                else None
            )
        )

        # حفظ Hash وليس كلمة المرور.
        user.set_password(
            form.password.data
        )

        db.session.add(user)
        db.session.commit()

        flash(
            "Account created successfully. "
            "Please log in.",
            "success"
        )

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "register.html",
        form=form
    )


@auth_blueprint.route(
    "/login",
    methods=["GET", "POST"]
)
def login():
    """تسجيل الدخول مع Remember Me."""

    if current_user.is_authenticated:
        return redirect(
            url_for("auth.dashboard")
        )

    form = LoginForm()

    if form.validate_on_submit():

        normalized_email = (
            form.email.data
            .strip()
            .lower()
        )

        user = db.session.scalar(
            select(User).where(
                User.email == normalized_email
            )
        )

        # رسالة عامة لا تكشف أي جزء كان خاطئًا.
        if (
            user is None
            or not user.check_password(
                form.password.data
            )
            or not user.is_active_account
        ):
            flash(
                "Invalid login information.",
                "error"
            )

            return render_template(
                "login.html",
                form=form
            )

        # إنشاء الجلسة المحفوظة.
        login_user(
            user,
            remember=form.remember_me.data,
            duration=timedelta(days=14)
        )

        # الجلسة العادية لها مدة محددة أيضًا.
        session.permanent = True

        return redirect(
            url_for("auth.dashboard")
        )

    return render_template(
        "login.html",
        form=form
    )


@auth_blueprint.post("/logout")
@login_required
def logout():
    """تسجيل خروج محمي بـCSRF."""

    form = LogoutForm()

    if form.validate_on_submit():
        logout_user()

        flash(
            "You have been logged out.",
            "success"
        )

        return redirect(
            url_for("auth.login")
        )

    return (
        "Invalid logout request.",
        400
    )


@auth_blueprint.get("/dashboard")
@login_required
def dashboard():
    """صفحة خاصة بالمستخدم المسجل."""

    logout_form = LogoutForm()

    from ..services.ramadan_service import get_active_ramadan_period
    from ..services.whatsapp_service import is_dry_run_enabled

    active_ramadan_period = get_active_ramadan_period()

    return render_template(
        "dashboard.html",
        logout_form=logout_form,
        active_ramadan_period=active_ramadan_period,
        whatsapp_dry_run=is_dry_run_enabled()
    )
