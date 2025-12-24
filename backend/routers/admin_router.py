from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from typing import List, Optional
from datetime import datetime, timedelta
from backend import database, models, schemas
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# ==============================================
# 🛠️ Helper Functions
# ==============================================

def get_current_user_id(token: str = Depends(oauth2_scheme)) -> int:
    """الحصول على user_id من التوكن"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def verify_admin(user_id: int, db: Session) -> models.User:
    """التحقق من أن المستخدم هو admin"""
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    if user.is_active != "active":
        raise HTTPException(status_code=403, detail="Account is inactive")
    return user

def get_admin_user(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(database.get_db)
) -> models.User:
    """Dependency للتحقق من صلاحيات admin"""
    return verify_admin(user_id, db)

# ==============================================
# 📊 Statistics & Dashboard
# ==============================================

@router.get("/stats")
def get_statistics(
    admin: models.User = Depends(get_admin_user),
    db: Session = Depends(database.get_db)
):
    """الحصول على إحصائيات شاملة"""
    try:
        # إحصائيات المستخدمين
        total_users = db.query(func.count(models.User.id)).scalar()
        active_users = db.query(func.count(models.User.id)).filter(
            models.User.is_active == "active"
        ).scalar()
        admin_users = db.query(func.count(models.User.id)).filter(
            models.User.role == "admin"
        ).scalar()
        
        # إحصائيات التحليلات
        total_analyses = db.query(func.count(models.SentimentResult.id)).scalar()
        
        # إحصائيات المشاعر
        sentiment_counts = db.query(
            models.SentimentResult.sentiment,
            func.count(models.SentimentResult.id).label('count')
        ).group_by(models.SentimentResult.sentiment).all()
        
        sentiment_stats = {sentiment.value: count for sentiment, count in sentiment_counts}
        
        # التحليلات اليوم
        today = datetime.utcnow() + timedelta(hours=3)
        today_start = today.replace(hour=0, minute=0, second=0, microsecond=0)
        today_analyses = db.query(func.count(models.SentimentResult.id)).filter(
            models.SentimentResult.timestamp >= today_start
        ).scalar()
        
        # التحليلات هذا الأسبوع
        week_start = today_start - timedelta(days=7)
        week_analyses = db.query(func.count(models.SentimentResult.id)).filter(
            models.SentimentResult.timestamp >= week_start
        ).scalar()
        
        return {
            "users": {
                "total": total_users,
                "active": active_users,
                "admins": admin_users,
                "inactive": total_users - active_users
            },
            "analyses": {
                "total": total_analyses,
                "today": today_analyses,
                "this_week": week_analyses
            },
            "sentiments": sentiment_stats
        }
    except Exception as e:
        logger.error(f"❌ Error getting statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching statistics")

# ==============================================
# 👥 User Management
# ==============================================

@router.get("/users", response_model=List[dict])
def get_all_users(
    admin: models.User = Depends(get_admin_user),
    db: Session = Depends(database.get_db),
    skip: int = 0,
    limit: int = 100
):
    """الحصول على قائمة جميع المستخدمين"""
    try:
        users = db.query(models.User).offset(skip).limit(limit).all()
        return [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active,
                "gender": user.gender,
                "date": str(user.date),
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "analyses_count": len(user.sentiments)
            }
            for user in users
        ]
    except Exception as e:
        logger.error(f"❌ Error getting users: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching users")

@router.get("/users/{user_id}")
def get_user_details(
    user_id: int,
    admin: models.User = Depends(get_admin_user),
    db: Session = Depends(database.get_db)
):
    """الحصول على تفاصيل مستخدم معين"""
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
            "gender": user.gender,
            "date": str(user.date),
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "analyses": [
                {
                    "id": s.id,
                    "text": s.text,
                    "sentiment": s.sentiment.value if hasattr(s.sentiment, 'value') else str(s.sentiment),
                    "confidence": s.confidence,
                    "timestamp": s.timestamp.isoformat()
                }
                for s in user.sentiments
            ],
            "analyses_count": len(user.sentiments)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting user details: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching user details")

@router.put("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    role: str,
    admin: models.User = Depends(get_admin_user),
    db: Session = Depends(database.get_db)
):
    """تحديث role المستخدم"""
    try:
        if role not in ["admin", "user"]:
            raise HTTPException(status_code=400, detail="Role must be 'admin' or 'user'")
        
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user.id == admin.id:
            raise HTTPException(status_code=400, detail="Cannot change your own role")
        
        user.role = role
        db.commit()
        db.refresh(user)
        
        logger.info(f"✅ Admin {admin.id} updated user {user_id} role to {role}")
        
        return {"message": f"User role updated to {role}", "user_id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating user role: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating user role")

@router.put("/users/{user_id}/status")
def update_user_status(
    user_id: int,
    status: str,
    admin: models.User = Depends(get_admin_user),
    db: Session = Depends(database.get_db)
):
    """تحديث حالة المستخدم (active/inactive)"""
    try:
        if status not in ["active", "inactive"]:
            raise HTTPException(status_code=400, detail="Status must be 'active' or 'inactive'")
        
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user.id == admin.id:
            raise HTTPException(status_code=400, detail="Cannot deactivate your own account")
        
        user.is_active = status
        db.commit()
        db.refresh(user)
        
        logger.info(f"✅ Admin {admin.id} updated user {user_id} status to {status}")
        
        return {"message": f"User status updated to {status}", "user_id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error updating user status: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating user status")

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    admin: models.User = Depends(get_admin_user),
    db: Session = Depends(database.get_db)
):
    """حذف مستخدم"""
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user.id == admin.id:
            raise HTTPException(status_code=400, detail="Cannot delete your own account")
        
        # حذف جميع تحليلات المستخدم أولاً
        db.query(models.SentimentResult).filter(
            models.SentimentResult.user_id == user_id
        ).delete()
        
        # حذف المستخدم
        db.delete(user)
        db.commit()
        
        logger.info(f"✅ Admin {admin.id} deleted user {user_id}")
        
        return {"message": "User deleted successfully", "user_id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting user: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error deleting user")

# ==============================================
# 📊 Analysis Management
# ==============================================

@router.get("/analyses", response_model=List[dict])
def get_all_analyses(
    admin: models.User = Depends(get_admin_user),
    db: Session = Depends(database.get_db),
    skip: int = 0,
    limit: int = 100
):
    """الحصول على جميع التحليلات"""
    try:
        analyses = db.query(models.SentimentResult).order_by(
            desc(models.SentimentResult.timestamp)
        ).offset(skip).limit(limit).all()
        
        return [
            {
                "id": a.id,
                "text": a.text,
                "sentiment": a.sentiment.value if hasattr(a.sentiment, 'value') else str(a.sentiment),
                "confidence": a.confidence,
                "timestamp": a.timestamp.isoformat(),
                "user_id": a.user_id,
                "username": a.user.username if a.user else "Unknown"
            }
            for a in analyses
        ]
    except Exception as e:
        logger.error(f"❌ Error getting analyses: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching analyses")

@router.delete("/analyses/{analysis_id}")
def delete_analysis(
    analysis_id: int,
    admin: models.User = Depends(get_admin_user),
    db: Session = Depends(database.get_db)
):
    """حذف تحليل"""
    try:
        analysis = db.query(models.SentimentResult).filter(
            models.SentimentResult.id == analysis_id
        ).first()
        
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        db.delete(analysis)
        db.commit()
        
        logger.info(f"✅ Admin {admin.id} deleted analysis {analysis_id}")
        
        return {"message": "Analysis deleted successfully", "analysis_id": analysis_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting analysis: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error deleting analysis")

@router.delete("/analyses/user/{user_id}")
def delete_user_analyses(
    user_id: int,
    admin: models.User = Depends(get_admin_user),
    db: Session = Depends(database.get_db)
):
    """حذف جميع تحليلات مستخدم معين"""
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        count = db.query(models.SentimentResult).filter(
            models.SentimentResult.user_id == user_id
        ).delete()
        
        db.commit()
        
        logger.info(f"✅ Admin {admin.id} deleted {count} analyses for user {user_id}")
        
        return {"message": f"Deleted {count} analyses", "user_id": user_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error deleting user analyses: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Error deleting user analyses")

