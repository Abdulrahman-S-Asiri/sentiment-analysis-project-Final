from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta, date
import os
import logging
from dotenv import load_dotenv

load_dotenv()

# ✅ إعداد logging
logger = logging.getLogger(__name__)

from backend.database import get_db
from backend import models, schemas

router = APIRouter()

# 🔐 إعداد التشفير
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 🔐 إعدادات التوكن
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    logger.warning("⚠️ SECRET_KEY not set in environment variables!")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))


# 🔐 إعداد OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# ==============================================
# 🛠️ دوال داخلية
# ==============================================

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
        return models.User(id=user_id)
    except JWTError:
        raise credentials_exception

# ==============================================
# 🔐 API Endpoints
# ==============================================

# 📝 إنشاء مستخدم جديد
@router.post("/register", response_model=dict)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        if db.query(models.User).filter(models.User.email == user.email).first():
            raise HTTPException(status_code=400, detail="Email already registered.")

        if db.query(models.User).filter(models.User.username == user.username).first():
            raise HTTPException(status_code=400, detail="Username already taken.")

        hashed_password = pwd_context.hash(user.password)
        
        # ✅ تحويل تاريخ من string إلى Date object
        date_obj = datetime.strptime(user.date, "%Y-%m-%d").date()

        new_user = models.User(
            username=user.username,
            email=user.email,
            password=hashed_password,
            date=date_obj,
            gender=user.gender,
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"✅ New user registered: {user.username} ({user.email})")

        return {"message": "User created successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error registering user: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during registration")

# 🧠 تسجيل الدخول + إصدار توكن
@router.post("/login", response_model=schemas.Token)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()

    if not db_user or not pwd_context.verify(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    access_token = create_access_token(
        data={"user_id": db_user.id, "role": db_user.role}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer", "role": db_user.role}
