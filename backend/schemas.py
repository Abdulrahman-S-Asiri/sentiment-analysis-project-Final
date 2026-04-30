from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime, date

# =====================================
# 🧍‍♂️ المستخدم
# =====================================

# 🔹 نموذج إدخال عند إنشاء مستخدم جديد
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    date: str  # تاريخ الميلاد أو التسجيل بصيغة نصية (YYYY-MM-DD)
    gender: str
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not v or len(v.strip()) < 3:
            raise ValueError("Username must be at least 3 characters")
        if len(v.strip()) > 50:
            raise ValueError("Username cannot exceed 50 characters")
        return v.strip()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v or len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v
    
    @field_validator('date')
    @classmethod
    def validate_date(cls, v: str) -> str:
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v
    
    @field_validator('gender')
    @classmethod
    def validate_gender(cls, v: str) -> str:
        allowed = ["male", "female", "other"]
        if v.lower() not in allowed:
            raise ValueError(f"Gender must be one of: {', '.join(allowed)}")
        return v.lower()

# 🔹 نموذج لتسجيل الدخول
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# 🔹 نموذج الاستجابة بعد إنشاء الحساب أو الحصول على معلومات المستخدم
class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    date: str
    gender: str

    class Config:
        from_attributes = True  # ✅ Pydantic v2: بديل orm_mode


# =====================================
# 🔐 التوكن
# =====================================

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# =====================================
# 💬 تحليل المشاعر
# =====================================

# 🔹 إدخال نص للتحليل
class TextInput(BaseModel):
    text: str

    @field_validator('text')
    @classmethod
    def validate_text(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Text cannot be empty")
        if len(v.strip()) > 1000:
            raise ValueError("Text cannot exceed 1000 characters")
        return v.strip()


class EmotionResult(BaseModel):
    label: str
    confidence: float


class TokenImportance(BaseModel):
    token: str
    importance: float


# 🔹 استجابة تحليل المشاعر
class SentimentResponse(BaseModel):
    text: str
    sentiment: str
    score: Optional[float] = None
    confidence: Optional[float] = None
    emotions: list[EmotionResult] = []
    explanations: dict[str, list[TokenImportance]] = {}
    timestamp: datetime

    class Config:
        from_attributes = True