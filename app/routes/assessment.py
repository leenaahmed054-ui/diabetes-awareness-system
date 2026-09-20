
# Blueprint يقسم التطبيق إلى أجزاء منظمة.
from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash
)

# حماية الصفحات بحيث لا يدخلها إلا المستخدم المسجل.
from flask_login import login_required, current_user

# استيراد قاعدة البيانات.
from app.extensions import db

# استيراد جداول الملف الصحي والتقييم.
from app.models import HealthProfile, Assessment, Notification

# استيراد نموذج إدخال البيانات.
from app.assessment_forms import AssessmentForm

# استيراد خدمة نموذج الذكاء الاصطناعي.
from app.services.prediction_service import DiabetesPredictionService

# استيراد محرك التوعية المنفصل عن نموذج التنبؤ.
from app.services.awareness_service import (
    create_complete_awareness
)


# إنشاء Blueprint خاص بالتقييمات.
assessment_bp = Blueprint(
    "assessment",
    __name__,
    url_prefix="/assessment"
)


# إنشاء خدمة التنبؤ مرة واحدة.
# تحميل ملف النموذج الفعلي يتم بصورة مؤجلة داخل الخدمة.
prediction_service = DiabetesPredictionService()


@assessment_bp.route("/new", methods=["GET", "POST"])
@login_required
def new_assessment():
    """
    عرض نموذج التقييم واستقبال بيانات المستخدم.

    لا تُعرض هذه الصفحة إلا بعد تسجيل الدخول.
    """

    form = AssessmentForm()

    # تنفيذ الكود التالي فقط بعد إرسال نموذج صحيح.
    if form.validate_on_submit():

        # قراءة الجنس من النموذج.
        gender = form.gender.data

        # النموذج تعلّم أن:
        # 0 = Male
        # 1 = Female
        gender_code = 1 if gender == "female" else 0

        # النشاط البدني:
        # 1 = Active
        # 0 = Not active
        physically_active = int(
            form.physically_active.data
        )

        # تطبيق منطق الحمل بناءً على الجنس.
        if gender == "male":
            pregnancy_status = "not_applicable"
            parity = None
        else:
            pregnancy_status = form.pregnancy_status.data
            parity = form.parity.data

        try:
            # إرسال المدخلات المطابقة تمامًا لميزات نموذج NHANES.
            prediction_result = prediction_service.predict(
                gender=gender,
                age=form.age.data,
                bmi=form.bmi.data,
                systolic_bp=form.systolic_bp.data,
                diastolic_bp=form.diastolic_bp.data,
                glucose=form.glucose.data,
                physically_active=physically_active
            )

            # البحث عن ملف صحي سابق للمستخدم.
            health_profile = HealthProfile.query.filter_by(
                user_id=current_user.id
            ).first()

            # إذا لم يكن للمستخدم ملف صحي، ننشئ واحدًا.
            if health_profile is None:
                health_profile = HealthProfile(
                    user_id=current_user.id
                )
                db.session.add(health_profile)

            # تحديث البيانات الحساسة للجنس والحمل.
            health_profile.gender = gender
            health_profile.pregnancy_status = pregnancy_status
            health_profile.parity = parity

            # إنشاء سجل جديد لكل عملية تقييم.
            assessment = Assessment(
                user_id=current_user.id,
                age=form.age.data,
                gender_code=gender_code,
                bmi=form.bmi.data,
                systolic_bp=form.systolic_bp.data,
                diastolic_bp=form.diastolic_bp.data,
                glucose=form.glucose.data,
                physically_active=physically_active,
                pregnancy_status=pregnancy_status,
                parity=parity,
                model_risk_score=prediction_result[
                    "model_risk_score"
                ],
                risk_level=prediction_result["risk_level"],
                predicted_class=prediction_result[
                    "predicted_class"
                ]
            )

            # إضافة التقييم إلى جلسة قاعدة البيانات.
            db.session.add(assessment)

            # flush يمنح التقييم ID من MySQL قبل commit.
            # نحتاج هذا الرقم لربط إشعار WhatsApp بالتقييم.
            db.session.flush()

            # إنشاء إشعار فقط إذا كانت جميع شروط
            # الموافقة والخصوصية متوفرة.
            if (
                current_user.is_active_account
                and current_user.whatsapp_consent
                and current_user.phone_number_encrypted
            ):
                # نص داخلي للتوثيق في MySQL.
                # الإرسال الفعلي يستخدم WhatsApp Template.
                notification_message = (
                    "Your diabetes awareness assessment is ready. "
                    f"Model risk score: "
                    f"{assessment.model_risk_score * 100:.2f}%. "
                    f"Risk level: {assessment.risk_level}. "
                    "This result is for awareness only and is not "
                    "a medical diagnosis."
                )

                assessment_notification = Notification(
                    user_id=current_user.id,
                    assessment_id=assessment.id,
                    notification_type="assessment_result",
                    message_text=notification_message,
                    delivery_status="pending"
                )

                db.session.add(assessment_notification)

            # حفظ الملف الصحي والتقييم والإشعار
            # داخل معاملة MySQL واحدة.
            db.session.commit()

            flash(
                "Your assessment was saved successfully.",
                "success"
            )

            # الانتقال إلى صفحة النتيجة.
            return redirect(
                url_for(
                    "assessment.assessment_result",
                    assessment_id=assessment.id
                )
            )

        except (ValueError, TypeError) as error:
            # أخطاء التحقق من المدخلات لا تكشف معلومات حساسة.
            db.session.rollback()

            flash(
                f"Please check the entered values: {error}",
                "danger"
            )

        except Exception:
            # التراجع عن أي تغييرات عند حدوث خطأ.
            db.session.rollback()

            # لا نعرض تفاصيل قاعدة البيانات للمستخدم.
            flash(
                "The assessment could not be completed. "
                "Please try again.",
                "danger"
            )

    return render_template(
        "assessment_form.html",
        form=form
    )


@assessment_bp.route("/<int:assessment_id>")
@login_required
def assessment_result(assessment_id):
    """
    عرض نتيجة تقييم واحدة.

    إضافة user_id إلى البحث تمنع ثغرة IDOR:
    لا يستطيع المستخدم مشاهدة نتيجة مستخدم آخر
    بتغيير رقم التقييم داخل رابط الصفحة.
    """

    assessment = Assessment.query.filter_by(
        id=assessment_id,
        user_id=current_user.id
    ).first_or_404()

    # تحويل GenderCode إلى اسم الجنس المستخدم
    # داخل محرك التوعية.
    gender = (
        "female"
        if assessment.gender_code == 1
        else "male"
    )

    # إنشاء رسائل BMI والنشاط والحمل.
    # هذه الرسائل توعوية ولا تغير نتيجة نموذج ML.
    awareness_messages = create_complete_awareness(
        gender=gender,
        bmi=assessment.bmi,
        physically_active=assessment.physically_active,
        pregnancy_status=assessment.pregnancy_status,
        parity=assessment.parity,
        systolic_bp=assessment.systolic_bp,
        diastolic_bp=assessment.diastolic_bp,
        glucose=assessment.glucose
    )

    # تمرير النتيجة والرسائل إلى صفحة HTML.
    return render_template(
        "assessment_result.html",
        assessment=assessment,
        awareness_messages=awareness_messages
    )


@assessment_bp.route("/history")
@login_required
def assessment_history():
    """
    عرض سجل تقييمات المستخدم الحالي فقط.
    """

    assessments = (
        Assessment.query
        .filter_by(user_id=current_user.id)
        .order_by(Assessment.created_at.desc())
        .all()
    )

    return render_template(
        "assessment_history.html",
        assessments=assessments
    )
