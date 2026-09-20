import os
from pathlib import Path

import joblib
import pandas as pd


# ترتيب الأعمدة المستخدم أثناء تدريب النموذج.
FINAL_MODEL_FEATURES = [
    "GenderCode",
    "Age",
    "BMI",
    "SystolicBP",
    "DiastolicBP",
    "Glucose",
    "PhysicallyActive"
]


class DiabetesPredictionService:
    """
    تحمل نموذج Machine Learning وتنفذ
    التنبؤات الخاصة بالموقع.
    """

    def __init__(self, model_path=None):

        # الوصول من services إلى مجلد web_app.
        project_root = (
            Path(__file__)
            .resolve()
            .parents[2]
        )

        # السماح بتحديد مسار مختلف عبر
        # Environment Variable عند الاستضافة.
        configured_model_path = os.getenv(
            "MODEL_PATH"
        )

        self.model_path = Path(
            model_path
            or configured_model_path
            or (
                project_root
                / "models"
                / (
                    "nhanes_inclusive_"
                    "diabetes_pipeline.joblib"
                )
            )
        )

        self._model = None

    def load_model(self):
        """
        تحميل النموذج مرة واحدة فقط،
        ثم الاحتفاظ به في الذاكرة.
        """

        if self._model is not None:
            return self._model

        if not self.model_path.exists():
            raise FileNotFoundError(
                "The diabetes model was not found at: "
                + str(self.model_path)
            )

        self._model = joblib.load(
            self.model_path
        )

        return self._model

    @staticmethod
    def classify_risk_level(risk_score):
        """
        تحويل Model Risk Score إلى
        Low أو Medium أو High.
        """

        if risk_score < 0.30:
            return "Low Risk"

        if risk_score < 0.70:
            return "Medium Risk"

        return "High Risk"

    @staticmethod
    def encode_gender(gender):
        """
        تحويل الجنس إلى نفس ترميز التدريب.
        """

        normalized_gender = (
            str(gender)
            .strip()
            .lower()
        )

        if normalized_gender == "male":
            return 0

        if normalized_gender == "female":
            return 1

        raise ValueError(
            "Gender must be Male or Female."
        )

    @staticmethod
    def encode_activity(physically_active):
        """
        تحويل النشاط إلى 0 أو 1.
        """

        if physically_active in [
            True, 1, "1", "Yes", "yes"
        ]:
            return 1

        if physically_active in [
            False, 0, "0", "No", "no"
        ]:
            return 0

        raise ValueError(
            "Physical activity must be Yes or No."
        )

    @staticmethod
    def validate_positive_number(
        field_name,
        value
    ):
        """
        التأكد أن القياس رقم موجب.
        """

        if value is None:
            raise ValueError(
                f"{field_name} is required."
            )

        try:
            numeric_value = float(value)

        except (ValueError, TypeError):
            raise ValueError(
                f"{field_name} must be numeric."
            )

        if numeric_value <= 0:
            raise ValueError(
                f"{field_name} must be "
                "greater than zero."
            )

        return numeric_value

    def predict(
        self,
        gender,
        age,
        bmi,
        systolic_bp,
        diastolic_bp,
        glucose,
        physically_active
    ):
        """
        إنشاء سجل مستخدم وتشغيل النموذج.
        """

        gender_code = self.encode_gender(
            gender
        )

        activity_code = self.encode_activity(
            physically_active
        )

        checked_age = (
            self.validate_positive_number(
                "Age",
                age
            )
        )

        checked_bmi = (
            self.validate_positive_number(
                "BMI",
                bmi
            )
        )

        checked_systolic = (
            self.validate_positive_number(
                "Systolic blood pressure",
                systolic_bp
            )
        )

        checked_diastolic = (
            self.validate_positive_number(
                "Diastolic blood pressure",
                diastolic_bp
            )
        )

        checked_glucose = (
            self.validate_positive_number(
                "Glucose",
                glucose
            )
        )

        user_data = pd.DataFrame([{
            "GenderCode": gender_code,
            "Age": checked_age,
            "BMI": checked_bmi,
            "SystolicBP": checked_systolic,
            "DiastolicBP": checked_diastolic,
            "Glucose": checked_glucose,
            "PhysicallyActive": activity_code
        }])

        # ضمان ترتيب الأعمدة.
        user_data = user_data[
            FINAL_MODEL_FEATURES
        ]

        model = self.load_model()

        risk_score = float(
            model.predict_proba(
                user_data
            )[0, 1]
        )

        predicted_class = int(
            model.predict(
                user_data
            )[0]
        )

        risk_level = (
            self.classify_risk_level(
                risk_score
            )
        )

        return {
            "predicted_class": predicted_class,

            "model_risk_score": round(
                risk_score,
                6
            ),

            "model_risk_percentage": round(
                risk_score * 100,
                2
            ),

            "risk_level": risk_level,

            "disclaimer": (
                "This result provides early "
                "awareness only and is not a "
                "medical diagnosis."
            )
        }


# نسخة واحدة يعاد استخدامها داخل الموقع.
prediction_service = (
    DiabetesPredictionService()
)
