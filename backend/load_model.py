from transformers import AutoTokenizer, AutoModelForSequenceClassification
from torch.nn.functional import sigmoid
import torch
import os
import json

MODEL_PATH = os.path.join(os.path.dirname(__file__), "../model")

tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
model.eval()

# Load labels from config.json
with open(os.path.join(MODEL_PATH, "config.json"), "r", encoding="utf-8") as f:
    config = json.load(f)
    id2label = {int(k): v for k, v in config.get("id2label", {}).items()}
    label2id = config.get("label2id", {})

# Load temperature for calibration
temp_path = os.path.join(MODEL_PATH, "temperature.pt")
temperature = 1.0
if os.path.exists(temp_path):
    temperature = torch.load(temp_path, map_location=device).get("temperature", 1.0)

# Load inference config (threshold, labels)
inference_config_path = os.path.join(MODEL_PATH, "inference_config.json")
emotion_threshold = 0.3
if os.path.exists(inference_config_path):
    with open(inference_config_path, "r") as f:
        inf_cfg = json.load(f)
        emotion_threshold = inf_cfg.get("threshold", 0.3)

# Fallback id2label if config doesn't have it (backward compat)
if not id2label:
    id2label = {
        0: "anger", 1: "disgust", 2: "fear", 3: "happiness",
        4: "sadness", 5: "surprise", 6: "neutral"
    }
    label2id = {v: k for k, v in id2label.items()}


def predict_emotion(text: str) -> dict:
    """Multi-label emotion prediction with calibrated confidence."""
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=128)
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        logits = model(**inputs).logits
        probs = sigmoid(logits / temperature)

    mask = probs[0] > emotion_threshold
    indices = torch.where(mask)[0].tolist()

    # Always include at least the top emotion
    if not indices:
        top_idx = torch.argmax(probs[0]).item()
        indices = [top_idx]

    emotions = []
    for idx in indices:
        emotions.append({
            "label": id2label.get(idx, f"class_{idx}"),
            "confidence": round(float(probs[0][idx].item()), 4)
        })

    emotions.sort(key=lambda x: x["confidence"], reverse=True)
    return {"emotions": emotions}


# SHAP explainer (lazy singleton)
_shap_explainer = None


def _get_shap_explainer():
    global _shap_explainer
    if _shap_explainer is not None:
        return _shap_explainer if _shap_explainer is not False else None

    try:
        import shap

        def pred_fn(texts):
            inputs = tokenizer(
                list(texts), return_tensors="pt",
                truncation=True, padding=True, max_length=128
            )
            inputs = {k: v.to(device) for k, v in inputs.items()}
            with torch.no_grad():
                logits = model(**inputs).logits
                return sigmoid(logits / temperature).cpu().numpy()

        output_names = [id2label[i] for i in range(len(id2label))]
        _shap_explainer = shap.Explainer(pred_fn, tokenizer, output_names=output_names)
    except Exception as e:
        print(f"SHAP init failed: {e}")
        _shap_explainer = False
    return _shap_explainer if _shap_explainer is not False else None


def explain_emotions(text: str, emotions: list) -> dict:
    """Generate SHAP token attributions for each predicted emotion."""
    explainer = _get_shap_explainer()
    if not explainer:
        return {}

    try:
        sv = explainer([text], max_evals=500)
        result = {}

        for em in emotions:
            label = em["label"]
            if label not in label2id:
                continue
            idx = label2id[label]
            values = sv.values[0, :, idx]
            tokens = sv.data[0]
            items = []
            for tok, val in zip(tokens, values):
                if abs(float(val)) > 0.005:
                    items.append({"token": str(tok), "importance": round(float(val), 4)})
            items.sort(key=lambda x: abs(x["importance"]), reverse=True)
            result[label] = items[:20]

        return result
    except Exception as e:
        print(f"SHAP explanation failed: {e}")
        return {}
