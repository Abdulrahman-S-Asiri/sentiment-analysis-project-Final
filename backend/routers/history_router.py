from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from backend import database, models, schemas
import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()

# ✅ إعداد logging
logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["History"]
)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

@router.get("/", response_model=list[schemas.SentimentResponse])
def get_user_history(
    db: Session = Depends(database.get_db),
    token: str = Depends(oauth2_scheme)
):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        results = db.query(models.SentimentResult).filter(
            models.SentimentResult.user_id == user_id
        ).order_by(models.SentimentResult.timestamp.desc()).all()

        logger.info(f"✅ Retrieved {len(results)} history records for user {user_id}")

        response = []
        for r in results:
            emotions = json.loads(r.emotions_json) if r.emotions_json else [
                {"label": r.sentiment, "confidence": r.confidence or 0}
            ]
            explanations = json.loads(r.explanations_json) if r.explanations_json else {}
            top = emotions[0] if emotions else {"label": r.sentiment, "confidence": 0.0}

            response.append(schemas.SentimentResponse(
                text=r.text,
                sentiment=top["label"],
                score=top["confidence"],
                confidence=top["confidence"],
                emotions=emotions,
                explanations=explanations,
                timestamp=r.timestamp
            ))

        return response

    except HTTPException:
        raise
    except JWTError:
        logger.warning("❌ Invalid JWT token in history endpoint")
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"❌ Error loading history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")