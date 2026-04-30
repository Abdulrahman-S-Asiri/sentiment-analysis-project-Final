from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, Date, Float, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from backend.database import Base
import enum

# ✅ تعريف Enum للمشاعر (يجب أن يتطابق مع النموذج)
class SentimentEnum(enum.Enum):
    sadness = "sadness"
    happiness = "happiness"  # ✅ تغيير من "joy" إلى "happiness" لتطابق النموذج
    anger = "anger"
    fear = "fear"
    neutral = "neutral"
    surprise = "surprise"
    disgust = "disgust"

# ✅ جدول المستخدمين
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    date = Column(Date, nullable=False)
    gender = Column(String(10), nullable=False)
    role = Column(String(20), default="user", nullable=False)  # ✅ إضافة role: admin أو user
    is_active = Column(String(10), default="active", nullable=False)  # ✅ active أو inactive
    created_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(hours=3))

    sentiments = relationship("SentimentResult", back_populates="user")

# ✅ جدول نتائج تحليل المشاعر
class SentimentResult(Base):
    __tablename__ = "sentiment_results"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String(1000), nullable=False)
    sentiment = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=True)
    emotions_json = Column(Text, nullable=True)
    explanations_json = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(hours=3))  # ✅ الوقت السعودي

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="sentiments")
