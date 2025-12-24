from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from backend import schemas, models, database
from backend.load_model import predict_emotion
import os
import logging
from dotenv import load_dotenv

load_dotenv()

# ✅ إعداد logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/predict",
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

        # ✅ تحليل النص باستخدام النموذج
        result_data = predict_emotion(input.text)
        sentiment = result_data["label"]
        confidence = result_data["confidence"]

        # ✅ التحقق من أن المشاعر موجودة في Enum
        try:
            sentiment_enum = models.SentimentEnum[sentiment]
        except KeyError:
            logger.error(f"❌ Invalid sentiment label from model: {sentiment}")
            raise HTTPException(
                status_code=500, 
                detail=f"Model returned invalid sentiment: {sentiment}"
            )

        # ✅ تخزين النتيجة في قاعدة البيانات
        result = models.SentimentResult(
            text=input.text,
            sentiment=sentiment_enum,
            confidence=confidence,
            user_id=user_id,
            timestamp=datetime.utcnow() + timedelta(hours=3)
        )

        db.add(result)
        db.commit()
        db.refresh(result)
        
        logger.info(f"✅ Prediction saved for user {user_id}: {sentiment} (confidence: {confidence:.2f})")

        return {
            "text": input.text,
            "sentiment": sentiment,
            "score": confidence,
            "confidence": confidence,
            "timestamp": result.timestamp
        }

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
