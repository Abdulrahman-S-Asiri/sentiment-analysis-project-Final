# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
from pathlib import Path
from dotenv import load_dotenv

# ✅ تحميل متغيرات البيئة
load_dotenv()

# ✅ تحديد مسار ملف قاعدة البيانات SQLite
BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE_FILE = os.getenv("DATABASE_FILE", "sentiment_db.sqlite")
DATABASE_PATH = BASE_DIR / DATABASE_FILE

# ✅ رابط الاتصال باستخدام SQLite
# check_same_thread=False مطلوب لـ SQLite مع FastAPI
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# ✅ إنشاء محرك قاعدة البيانات
# connect_args={"check_same_thread": False} مطلوب لـ SQLite مع FastAPI
engine = create_engine(
    DATABASE_URL,
    echo=True,
    connect_args={"check_same_thread": False}  # ✅ مطلوب لـ SQLite
)

# إعداد الجلسة
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# تعريف الأساس لإنشاء الجداول
Base = declarative_base()

# دالة لإرجاع الجلسة في كل طلب
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# اختبار الاتصال بقاعدة البيانات (اختياري)
import logging
logger = logging.getLogger(__name__)

try:
    with engine.connect() as connection:
        logger.info(f"✅ SQLite database connection successful! Database file: {DATABASE_PATH}")
except Exception as e:
    logger.error(f"❌ Database connection error: {e}")
    # لا نرفع الاستثناء هنا حتى لا يمنع التطبيق من البدء
