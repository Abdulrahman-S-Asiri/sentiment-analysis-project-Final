from transformers import AutoTokenizer, AutoModelForSequenceClassification
from torch.nn.functional import softmax
import torch
import os
import json

# تحديد مسار مجلد النموذج
MODEL_PATH = os.path.join(os.path.dirname(__file__), "../model")

# تحميل التوكنرايزر والموديل المدرب
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)

# تحديد الجهاز المناسب (GPU أو CPU)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()

# ✅ قراءة التسميات من ملف config.json للنموذج لضمان التطابق
CONFIG_PATH = os.path.join(MODEL_PATH, "config.json")
try:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)
        # تحويل id2label من النموذج إلى dictionary
        id2label_dict = config.get("id2label", {})
        id2label = {int(k): v for k, v in id2label_dict.items()}
except Exception as e:
    # في حالة فشل القراءة، استخدام القيم الافتراضية من النموذج
    print(f"⚠️ Warning: Could not read config.json, using model's id2label: {e}")
    id2label = {
        0: "happiness",  # ✅ تطابق مع config.json
        1: "sadness",
        2: "anger",
        3: "fear",
        4: "surprise",
        5: "disgust",
        6: "neutral"
    }

# دالة توقع المشاعر + الثقة
def predict_emotion(text: str) -> dict:
    # تجهيز الإدخال للنموذج
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    inputs = {k: v.to(device) for k, v in inputs.items()}

    # تنفيذ التنبؤ
    with torch.no_grad():
        outputs = model(**inputs)
        probs = softmax(outputs.logits, dim=1)
        predicted_class = torch.argmax(probs, dim=1).item()
        confidence = probs[0][predicted_class].item()

    return {
        "label": id2label[predicted_class],
        "confidence": confidence
    }
