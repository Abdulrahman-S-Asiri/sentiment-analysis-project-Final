from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from backend import schemas, models, database
from backend.load_model import predict_emotion, explain_emotions
import os
import json
import logging
from dotenv import load_dotenv

load_dotenv()

# ✅ إعداد logging
logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Prediction"]
)

# 🔐 إعداد التوكن
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

@router.post("/", response_model=schemas.SentimentResponse)
def predict(
    input: schemas.TextInput,
    db: Session = Depends(database.get_db),
    token: str = Depends(oauth2_scheme)
):
    try:
        # ✅ فك التوكن والتحقق
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")

        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        # ✅ تحليل النص باستخدام النموذج (multi-label)
        result_data = predict_emotion(input.text)
        emotions = result_data["emotions"]

        top_emotion = emotions[0] if emotions else {"label": "neutral", "confidence": 0.0}

        # ✅ تخزين النتيجة في قاعدة البيانات
        result = models.SentimentResult(
            text=input.text,
            sentiment=top_emotion["label"],
            confidence=top_emotion["confidence"],
            emotions_json=json.dumps(emotions),
            user_id=user_id,
            timestamp=datetime.utcnow() + timedelta(hours=3)
        )

        db.add(result)
        db.commit()
        db.refresh(result)

        logger.info(f"✅ Prediction saved for user {user_id}: {[e['label'] for e in emotions]}")

        # SHAP explanations (computed after DB write; if it fails, result still valid)
        explanations = {}
        try:
            explanations = explain_emotions(input.text, emotions)
            if explanations:
                result.explanations_json = json.dumps(explanations)
                db.commit()
        except Exception as e:
            logger.warning(f"SHAP explanation failed (non-fatal): {e}")

        return schemas.SentimentResponse(
            text=input.text,
            sentiment=top_emotion["label"],
            score=top_emotion["confidence"],
            confidence=top_emotion["confidence"],
            emotions=emotions,
            explanations=explanations,
            timestamp=result.timestamp
        )

    except HTTPException:
        raise
    except JWTError:
        logger.warning("❌ Invalid JWT token in predict endpoint")
        raise HTTPException(status_code=401, detail="Invalid token")
    except ValueError as e:
        logger.error(f"❌ Validation error in /predict: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Error in /predict: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")
