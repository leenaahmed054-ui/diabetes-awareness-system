from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect


# إدارة قاعدة البيانات.
db = SQLAlchemy()

# إدارة تسجيل الدخول والجلسات.
login_manager = LoginManager()

# حماية النماذج من CSRF.
csrf = CSRFProtect()
