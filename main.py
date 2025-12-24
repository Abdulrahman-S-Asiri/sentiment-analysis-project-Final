# main.py
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from pydantic import BaseModel
from pathlib import Path
import os
import logging

# ✅ إعداد logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ✅ تحميل .env
from dotenv import load_dotenv
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# ✅ استدعاء قاعدة البيانات والراوترات
from backend.database import Base, engine
from backend.routers import auth, predict_router, history_router, admin_router

# ✅ إنشاء التطبيق
app = FastAPI(title="Sentiment Analysis API", version="1.0.0")

# ✅ إعداد CORS (يمكن تخصيصه من متغيرات البيئة)
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # ✅ تقييد الأصول المسموحة
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# ✅ إعداد القوالب والملفات الثابتة
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
templates = Jinja2Templates(directory="frontend")

# ✅ إنشاء الجداول
try:
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables created successfully")
except Exception as e:
    logger.error(f"❌ Error creating database tables: {str(e)}")

# ✅ تسجيل الراوترات
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(history_router.router, prefix="/history", tags=["History"])
app.include_router(predict_router.router, prefix="/predict", tags=["Prediction"])
app.include_router(admin_router.router, tags=["Admin"])

# ✅ تعديل واجهة التوثيق (Swagger UI) لدعم Bearer Token
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Sentiment Analysis API",
        version="1.0.0",
        description="تحليل المشاعر باستخدام موديل مدرب من 7 مشاعر.",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            if "security" not in openapi_schema["paths"][path][method]:
                openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# ✅ نموذج إدخال نص
class TextIn(BaseModel):
    text: str

# ✅ Endpoints أساسية
@app.get("/")
def root():
    return {"message": "Sentiment API is running", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "ok", "env": os.getenv("APP_ENV")}

# ✅ تم حذف endpoint المكرر - يتم التعامل معه من خلال predict_router

# ✅ صفحات HTML
@app.get("/home", response_class=HTMLResponse)
def get_home(request: Request):
    return templates.TemplateResponse("front.html", {"request": request})

@app.get("/analyze", response_class=HTMLResponse)
def analyze_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("registration.html", {"request": request})

@app.get("/history-page", response_class=HTMLResponse)
def history_page(request: Request):
    return templates.TemplateResponse("history.html", {"request": request})

@app.get("/about", response_class=HTMLResponse)
def about_page(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})
