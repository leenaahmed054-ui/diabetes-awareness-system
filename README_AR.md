# حزمة واجهة مشروع السكري

هذه الحزمة مبنية فوق مشروع Flask الحقيقي وتحافظ على أسماء الحقول والمسارات الحالية.

## ما تم ربطه

- تسجيل الحساب والدخول والخروج عبر Routes الأصلية.
- نموذج التقييم يرسل نفس حقول WTForms إلى `DiabetesPredictionService`.
- النتيجة المعروضة هي الدرجة المحفوظة من النموذج، وليست معادلة JavaScript تجريبية.
- تحليل منفصل للتوعية: BMI، ضغط الدم، الجلوكوز، النشاط البدني، والحمل للإناث.
- زر حفظ التقرير PDF باستخدام نافذة الطباعة في المتصفح.
- تبديل عربي/إنجليزي، مع إرسال الأرقام إلى الخادم بصيغة لاتينية صحيحة.
- إخفاء أسئلة الحمل للذكر، وإظهارها للأنثى.

## التركيب في Google Colab

1. ارفعي ملف ZIP الناتج إلى جلسة Colab.
2. عدّلي `ZIP_PATH` إذا كان اسم الملف أو مكانه مختلفًا.
3. شغّلي الخلية التالية مرة واحدة:

```python
from pathlib import Path
from datetime import datetime
import shutil
import zipfile

PROJECT = Path("/content/drive/MyDrive/Diabetes_Graduation_Project/web_app")
ZIP_PATH = Path("/content/Diabetes_Flask_UI_Integrated.zip")

if not (PROJECT / "app").is_dir():
    raise FileNotFoundError(f"Project not found: {PROJECT}")
if not ZIP_PATH.is_file():
    raise FileNotFoundError(f"ZIP not found: {ZIP_PATH}")

stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = PROJECT / f"ui_backend_backup_{stamp}"
backup.mkdir(parents=True)

for relative in [
    "app/templates",
    "app/static",
    "app/routes/assessment.py",
    "app/services/awareness_service.py",
]:
    source = PROJECT / relative
    if source.exists():
        destination = backup / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, destination, dirs_exist_ok=True)
        else:
            shutil.copy2(source, destination)

with zipfile.ZipFile(ZIP_PATH) as archive:
    archive.extractall(PROJECT)

print("تم التركيب بنجاح")
print("النسخة الاحتياطية:", backup)
```

4. أعيدي تشغيل خلية إعداد متغيرات البيئة وقاعدة البيانات في جلسة Colab.
5. شغّلي Flask بدون reloader، ثم افتحيه عبر رابط النفق الذي تستخدمه زميلتك.

```python
%cd /content/drive/MyDrive/Diabetes_Graduation_Project/web_app
!python -m compileall -q app
!python run.py
```

إذا كانت خلية تشغيل السيرفر لدى زميلتك تستخدم `cloudflared` أو `ngrok`، استخدميها بدل السطر الأخير. رابط `127.0.0.1` لا يفتح مباشرة من جهازك خارج Colab.

## ملاحظات مهمة

- لا تحتوي الحزمة على `.env` ولا `config.py`، لذلك لا تستبدل الأسرار.
- الجلوكوز يعرض تنبيهًا عامًا لأن النموذج الحالي لا يسجل هل القياس صائم أم عشوائي.
- زر PDF يفتح نافذة الطباعة؛ اختاري **Save as PDF / حفظ كملف PDF**.
- المحتوى توعوي وليس تشخيصًا طبيًا.
