import os

from app import create_app


# إنشاء التطبيق عن طريق App Factory.
app = create_app()


if __name__ == "__main__":

    # debug يعمل فقط أثناء التطوير.
    # في الاستضافة لن نستخدم Flask Development Server.
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        debug=(os.getenv("FLASK_DEBUG", "false").lower() == "true"),
        use_reloader=False
    )
