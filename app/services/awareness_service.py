
"""
Smart Awareness Engine.

هذه الخدمة لا تشخّص مرض السكري ولا تقترح علاجًا.
وظيفتها إنشاء رسائل توعوية عامة بناءً على بيانات المستخدم.
"""


# روابط المصادر الرسمية المستخدمة في صياغة التوعية.
WHO_BMI_SOURCE = (
    "https://www.who.int/news-room/fact-sheets/"
    "detail/obesity-and-overweight"
)

WHO_ACTIVITY_SOURCE = (
    "https://www.who.int/news-room/fact-sheets/"
    "detail/physical-activity"
)

CDC_GESTATIONAL_DIABETES_SOURCE = (
    "https://www.cdc.gov/diabetes/about/"
    "about-gestational-diabetes.html"
)


def classify_bmi(bmi):
    """
    تصنيف BMI للبالغين إلى فئات توعوية عامة.

    الحدود:
    أقل من 18.5        = Underweight
    من 18.5 إلى 24.9  = Healthy range
    من 25 إلى 29.9    = Overweight
    30 أو أكثر         = Obesity range
    """

    # تحويل القيمة إلى float لضمان إمكانية مقارنتها.
    bmi = float(bmi)

    # رفض القيم غير المنطقية قبل إنشاء الرسالة.
    if bmi <= 0:
        raise ValueError("BMI must be greater than zero.")

    if bmi < 18.5:
        return "Underweight"

    if bmi < 25:
        return "Healthy range"

    if bmi < 30:
        return "Overweight"

    return "Obesity range"


def create_bmi_awareness(bmi):
    """
    إنشاء رسالة توعوية مناسبة لفئة BMI.
    """

    bmi_category = classify_bmi(bmi)

    if bmi_category == "Underweight":
        message = (
            "Your BMI is below the general healthy adult range. "
            "Consider discussing nutrition and weight changes "
            "with a qualified healthcare professional."
        )

    elif bmi_category == "Healthy range":
        message = (
            "Your BMI is within the general healthy adult range. "
            "Maintaining balanced nutrition and regular activity "
            "can support overall health."
        )

    elif bmi_category == "Overweight":
        message = (
            "Your BMI is within the overweight range. "
            "Small sustainable improvements in nutrition and "
            "physical activity may help reduce health risks."
        )

    else:
        message = (
            "Your BMI is within the obesity range. "
            "Consider speaking with a qualified healthcare "
            "professional about safe and realistic health goals."
        )

    return {
        "category": "bmi",
        "title": "BMI awareness",
        "level": "information",
        "bmi_category": bmi_category,
        "message": message,
        "source": WHO_BMI_SOURCE
    }


def create_activity_awareness(physically_active):
    """
    إنشاء رسالة توعوية بناءً على حالة النشاط البدني.

    physically_active يجب أن تكون:
    1 = Active
    0 = Not active
    """

    activity_code = int(physically_active)

    if activity_code not in {0, 1}:
        raise ValueError(
            "Physical activity must be either 0 or 1."
        )

    if activity_code == 1:
        message = (
            "Continue maintaining regular physical activity. "
            "The type and intensity should remain appropriate "
            "for your health condition."
        )

    else:
        message = (
            "Regular physical activity can support general health "
            "and diabetes risk reduction. Start gradually and "
            "seek professional advice if you have a medical "
            "condition or pregnancy."
        )

    return {
        "category": "physical_activity",
        "title": "Physical activity awareness",
        "level": "information",
        "message": message,
        "source": WHO_ACTIVITY_SOURCE
    }


def create_blood_pressure_awareness(systolic_bp, diastolic_bp):
    """Create a general adult blood-pressure awareness message."""
    systolic = float(systolic_bp)
    diastolic = float(diastolic_bp)

    if systolic >= 180 or diastolic >= 120:
        level = "urgent"
        category = "Very high reading"
        message = (
            "This blood-pressure reading is very high. Repeat the measurement "
            "after resting and seek prompt medical advice. If you have chest "
            "pain, breathing difficulty, weakness, vision change, or confusion, "
            "seek emergency care immediately."
        )
    elif systolic >= 140 or diastolic >= 90:
        level = "important"
        category = "High range"
        message = (
            "The recorded blood pressure is in a high range. One reading does "
            "not establish a diagnosis; arrange repeated measurements and discuss "
            "them with a qualified healthcare professional."
        )
    elif systolic >= 130 or diastolic >= 80:
        level = "attention"
        category = "Above the general healthy range"
        message = (
            "The recorded blood pressure is above the general healthy adult "
            "range. Regular monitoring and healthy lifestyle habits are advisable."
        )
    elif systolic < 90 or diastolic < 60:
        level = "attention"
        category = "Low range"
        message = (
            "The recorded blood pressure is in a low range. If you have dizziness, "
            "fainting, or unusual weakness, consult a healthcare professional."
        )
    else:
        level = "information"
        category = "General healthy range"
        message = (
            "The recorded blood pressure is within the general healthy adult range. "
            "Continue periodic checks and healthy lifestyle habits."
        )

    return {
        "category": "blood_pressure",
        "title": "Blood pressure awareness",
        "level": level,
        "value_category": category,
        "message": message,
        "source": "https://www.heart.org/en/health-topics/high-blood-pressure/understanding-blood-pressure-readings"
    }


def create_glucose_awareness(glucose):
    """Explain the glucose value without treating it as a diagnosis."""
    value = float(glucose)
    return {
        "category": "glucose",
        "title": "Glucose awareness",
        "level": "important" if value >= 200 else "information",
        "value_category": "Requires measurement context",
        "message": (
            "A glucose value must be interpreted according to whether the sample "
            "was fasting, random, or part of a formal test. This application does "
            "not record that context, so the value cannot diagnose diabetes. "
            "Discuss an unexpected result with a qualified healthcare professional."
        ),
        "source": "https://diabetes.org/about-diabetes/diagnosis"
    }


def create_pregnancy_awareness(
    gender,
    pregnancy_status,
    parity=None
):
    """
    إنشاء رسالة خاصة بالجنس والحمل.

    الحمل لا يُستخدم داخل نموذج NHANES العام.
    هذه الرسالة منفصلة لتجنب اعتبار النتيجة تشخيصًا
    لسكري الحمل.
    """

    normalized_gender = str(gender).strip().lower()

    normalized_status = (
        str(pregnancy_status).strip().lower()
    )

    if normalized_gender not in {"male", "female"}:
        raise ValueError(
            "Gender must be male or female."
        )

    # حالة الحمل لا تنطبق على الذكر.
    if normalized_gender == "male":
        return {
            "category": "pregnancy",
            "title": "Pregnancy awareness",
            "level": "not_applicable",
            "message": (
                "Pregnancy-specific awareness is not applicable."
            ),
            "source": CDC_GESTATIONAL_DIABETES_SOURCE
        }

    # رسالة ذات أولوية للمرأة الحامل.
    if normalized_status == "pregnant":
        return {
            "category": "pregnancy",
            "title": "Pregnancy and glucose awareness",
            "level": "important",
            "message": (
                "Pregnancy requires pregnancy-specific medical "
                "assessment. This website's general diabetes model "
                "cannot diagnose gestational diabetes. Please "
                "follow the glucose screening schedule recommended "
                "by your obstetric or healthcare professional."
            ),
            "source": CDC_GESTATIONAL_DIABETES_SOURCE
        }

    # رسالة للأنثى غير الحامل.
    if normalized_status == "not_pregnant":
        parity_text = ""

        if parity is not None:
            parity_text = (
                f" The recorded number of previous pregnancies "
                f"is {int(parity)}."
            )

        return {
            "category": "pregnancy",
            "title": "Women's health awareness",
            "level": "information",
            "message": (
                "No current pregnancy was reported."
                + parity_text
                + " Pregnancy information is stored separately "
                  "from the general prediction model."
            ),
            "source": CDC_GESTATIONAL_DIABETES_SOURCE
        }

    # إذا لم ترغب المستخدمة في تقديم حالة الحمل.
    if normalized_status == "not_collected":
        return {
            "category": "pregnancy",
            "title": "Pregnancy information",
            "level": "information",
            "message": (
                "Pregnancy status was not provided. "
                "If you are pregnant, the general model result "
                "should not be used to assess gestational diabetes."
            ),
            "source": CDC_GESTATIONAL_DIABETES_SOURCE
        }

    raise ValueError(
        "A valid pregnancy status is required for female users."
    )


def create_complete_awareness(
    gender,
    bmi,
    physically_active,
    pregnancy_status,
    parity=None,
    systolic_bp=None,
    diastolic_bp=None,
    glucose=None
):
    """
    تجميع جميع رسائل التوعية في قائمة واحدة.

    هذا يسهل عرضها في صفحة النتيجة وإرسالها لاحقًا
    عبر WhatsApp بعد موافقة المستخدم.
    """

    awareness_messages = [
        create_bmi_awareness(bmi),
        create_activity_awareness(physically_active),
    ]

    if systolic_bp is not None and diastolic_bp is not None:
        awareness_messages.append(
            create_blood_pressure_awareness(systolic_bp, diastolic_bp)
        )

    if glucose is not None:
        awareness_messages.append(create_glucose_awareness(glucose))

    awareness_messages.append(
        create_pregnancy_awareness(
            gender=gender,
            pregnancy_status=pregnancy_status,
            parity=parity
        )
    )

    return awareness_messages
