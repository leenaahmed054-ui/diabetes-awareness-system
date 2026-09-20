
# FlaskForm يحمي النموذج باستخدام CSRF.
from flask_wtf import FlaskForm

# حقول النموذج التي سيملؤها المستخدم.
from wtforms import (
    SelectField,
    IntegerField,
    FloatField,
    SubmitField
)

# أدوات التحقق من صحة القيم المدخلة.
from wtforms.validators import (
    DataRequired,
    Optional,
    NumberRange,
    ValidationError
)


class AssessmentForm(FlaskForm):
    """
    نموذج إدخال البيانات المستخدمة في تقدير خطر السكري.

    النتيجة توعوية فقط وليست تشخيصًا طبيًا.
    """

    # جنس المستخدم مهم لتطبيق منطق الحمل بصورة صحيحة.
    gender = SelectField(
        "Gender",
        choices=[
            ("male", "Male"),
            ("female", "Female")
        ],
        validators=[DataRequired()]
    )

    # بيانات NHANES المستخدمة في النموذج تشمل البالغين فقط.
    age = IntegerField(
        "Age",
        validators=[
            DataRequired(),
            NumberRange(
                min=18,
                max=100,
                message="Age must be between 18 and 100."
            )
        ]
    )

    # مؤشر كتلة الجسم أحد مدخلات نموذج التنبؤ.
    bmi = FloatField(
        "BMI",
        validators=[
            DataRequired(),
            NumberRange(
                min=10,
                max=80,
                message="BMI must be between 10 and 80."
            )
        ]
    )

    # ضغط الدم الانقباضي.
    systolic_bp = FloatField(
        "Systolic blood pressure",
        validators=[
            DataRequired(),
            NumberRange(
                min=60,
                max=260,
                message="Systolic pressure must be between 60 and 260."
            )
        ]
    )

    # ضغط الدم الانبساطي.
    diastolic_bp = FloatField(
        "Diastolic blood pressure",
        validators=[
            DataRequired(),
            NumberRange(
                min=30,
                max=160,
                message="Diastolic pressure must be between 30 and 160."
            )
        ]
    )

    # مستوى الجلوكوز الذي سيستخدمه نموذج التنبؤ.
    glucose = FloatField(
        "Glucose",
        validators=[
            DataRequired(),
            NumberRange(
                min=40,
                max=600,
                message="Glucose must be between 40 and 600."
            )
        ]
    )

    # تحويل النشاط البدني لاحقًا إلى 1 للنشط و0 لغير النشط.
    physically_active = SelectField(
        "Physically active",
        choices=[
            ("1", "Yes"),
            ("0", "No")
        ],
        validators=[DataRequired()]
    )

    # حالة الحمل تُستخدم في محرك التوعية المنفصل.
    # لا نرسلها إلى نموذج NHANES لأنه لم يُدرّب عليها.
    pregnancy_status = SelectField(
        "Pregnancy status",
        choices=[
            ("not_applicable", "Not applicable"),
            ("not_pregnant", "Not pregnant"),
            ("pregnant", "Pregnant"),
            ("not_collected", "Prefer not to say")
        ],
        validators=[DataRequired()]
    )

    # عدد مرات الحمل خاص بالإناث واختياري.
    parity = IntegerField(
        "Number of previous pregnancies",
        validators=[
            Optional(),
            NumberRange(
                min=0,
                max=20,
                message="Pregnancy count must be between 0 and 20."
            )
        ]
    )

    # زر إرسال النموذج.
    submit = SubmitField("Calculate model risk score")

    def validate_pregnancy_status(self, field):
        """
        تطبيق التحقق المرتبط بالجنس.

        الذكر لا يمكنه اختيار حالة حامل،
        والأنثى لا ينبغي أن تختار Not applicable.
        """

        if self.gender.data == "male" and field.data == "pregnant":
            raise ValidationError(
                "Pregnancy status cannot be pregnant for a male user."
            )

        if self.gender.data == "female" and field.data == "not_applicable":
            raise ValidationError(
                "Please select the appropriate pregnancy status."
            )

    def validate_parity(self, field):
        """
        منع تسجيل عدد مرات الحمل للذكور.
        """

        if self.gender.data == "male" and field.data is not None:
            raise ValidationError(
                "Pregnancy count is only applicable to female users."
            )
