"""
Multi-label emotion classification training pipeline.

Trains a RoBERTa model on GoEmotions (28 labels -> 7 Ekman emotions)
with BCE loss, then computes temperature scaling for calibration.
Saves model + tokenizer + temperature to ../model/
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    get_linear_schedule_with_warmup,
)
from datasets import load_dataset
from tqdm import tqdm
import numpy as np
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = PROJECT_ROOT / "model"

# GoEmotions 28 labels
GOEMOTIONS_LABELS = [
    "admiration", "amusement", "anger", "annoyance", "approval",
    "caring", "confusion", "curiosity", "desire", "disappointment",
    "disapproval", "disgust", "embarrassment", "excitement", "fear",
    "gratitude", "grief", "joy", "love", "nervousness",
    "optimism", "pride", "realization", "relief", "remorse",
    "sadness", "surprise", "neutral",
]

# Map GoEmotions label names -> 7 Ekman emotion indices
_EKMAN_LABELS = ["anger", "disgust", "fear", "happiness", "sadness", "surprise", "neutral"]

_EKMAN_SETS = {
    "anger":     {"anger", "annoyance", "disapproval"},
    "disgust":   {"disgust"},
    "fear":      {"fear", "nervousness"},
    "happiness": {"joy", "amusement", "approval", "caring", "excitement",
                  "gratitude", "love", "optimism", "pride", "relief"},
    "sadness":   {"sadness", "disappointment", "embarrassment", "grief", "remorse"},
    "surprise":  {"surprise", "curiosity", "realization", "confusion"},
    "neutral":   {"neutral"},
}

# Precompute: for each GoEmotions index, which Ekman index (0-6) it maps to, or -1 if unmapped
_GOEMOTION_TO_EKMAN = []
for go_label in GOEMOTIONS_LABELS:
    found = -1
    for ek_idx, ek_label in enumerate(_EKMAN_LABELS):
        if go_label in _EKMAN_SETS[ek_label]:
            found = ek_idx
            break
    _GOEMOTION_TO_EKMAN.append(found)

ID2LABEL = {i: label for i, label in enumerate(_EKMAN_LABELS)}
LABEL2ID = {label: i for i, label in enumerate(_EKMAN_LABELS)}
NUM_LABELS = len(_EKMAN_LABELS)


def map_to_ekman(batch):
    """Convert GoEmotions label IDs to 7-class multi-hot vectors."""
    multi_hot = []
    for label_ids in batch["labels"]:
        vec = [0] * NUM_LABELS
        for lid in label_ids:
            ek_idx = _GOEMOTION_TO_EKMAN[lid]
            if ek_idx >= 0:
                vec[ek_idx] = 1
        multi_hot.append(vec)
    return {"ekman_labels": multi_hot}


def compute_metrics(y_true, y_pred, threshold=0.3):
    """Per-label and macro metrics."""
    y_pred_bin = (y_pred > threshold).astype(int)
    metrics = {}
    for i, label in enumerate(_EKMAN_LABELS):
        if y_true[:, i].sum() == 0:
            continue
        metrics[f"{label}_precision"] = precision_score(y_true[:, i], y_pred_bin[:, i], zero_division=0)
        metrics[f"{label}_recall"] = recall_score(y_true[:, i], y_pred_bin[:, i], zero_division=0)
        metrics[f"{label}_f1"] = f1_score(y_true[:, i], y_pred_bin[:, i], zero_division=0)
        try:
            metrics[f"{label}_auc"] = roc_auc_score(y_true[:, i], y_pred[:, i])
        except ValueError:
            metrics[f"{label}_auc"] = 0.5

    metrics["macro_f1"] = f1_score(y_true, y_pred_bin, average="macro", zero_division=0)
    metrics["micro_f1"] = f1_score(y_true, y_pred_bin, average="micro", zero_division=0)
    try:
        metrics["macro_auc"] = roc_auc_score(y_true, y_pred, average="macro")
    except ValueError:
        metrics["macro_auc"] = 0.5
    return metrics


def find_temperature(model, val_loader, device):
    """Optimize a single temperature scalar on validation set."""
    logger.info("Computing temperature scaling...")
    model.eval()
    all_logits, all_labels = [], []

    with torch.no_grad():
        for batch in tqdm(val_loader, desc="Collecting logits"):
            inputs = {k: v.to(device) for k, v in batch.items()
                      if k in ("input_ids", "attention_mask")}
            logits = model(**inputs).logits.cpu()
            all_logits.append(logits)
            all_labels.append(batch["ekman_labels"].cpu())

    logits = torch.cat(all_logits)
    labels = torch.cat(all_labels)

    T = nn.Parameter(torch.ones(1))
    optimizer = torch.optim.LBFGS([T], lr=0.01, max_iter=100)

    def closure():
        optimizer.zero_grad()
        loss = F.binary_cross_entropy_with_logits(logits / T, labels.float())
        loss.backward()
        return loss

    optimizer.step(closure)
    T_val = round(T.item(), 4)
    logger.info(f"Optimal temperature: {T_val}")
    return T_val


def train(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")

    # Load dataset
    logger.info("Loading GoEmotions dataset...")
    dataset = load_dataset("go_emotions", "raw")

    # Map labels
    dataset = dataset.map(map_to_ekman, batched=True)

    # Filter out samples with no Ekman labels (only admiration/desire)
    def has_labels(example):
        return sum(example["ekman_labels"]) > 0

    train_ds = dataset["train"].filter(has_labels)
    val_ds = dataset["validation"].filter(has_labels)
    test_ds = dataset["test"].filter(has_labels)

    logger.info(f"Train: {len(train_ds)}, Val: {len(val_ds)}, Test: {len(test_ds)}")

    # Load tokenizer and model
    logger.info(f"Loading {args.model_name}...")
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model_name,
        num_labels=NUM_LABELS,
        problem_type="multi_label_classification",
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )
    model.to(device)

    # Tokenize
    def tokenize_fn(batch):
        return tokenizer(batch["text"], truncation=True, padding="max_length", max_length=128)

    train_ds = train_ds.map(tokenize_fn, batched=True, batch_size=1000)
    val_ds = val_ds.map(tokenize_fn, batched=True, batch_size=1000)
    test_ds = test_ds.map(tokenize_fn, batched=True, batch_size=1000)

    columns = ["input_ids", "attention_mask", "ekman_labels"]
    train_ds.set_format("torch", columns=columns)
    val_ds.set_format("torch", columns=columns)
    test_ds.set_format("torch", columns=columns)

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size * 2, shuffle=False)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size * 2, shuffle=False)

    # Compute class weights for imbalance
    all_train_labels = torch.cat([batch["ekman_labels"] for batch in train_loader])
    pos_counts = all_train_labels.sum(dim=0)
    neg_counts = len(train_ds) - pos_counts
    pos_weight = neg_counts / (pos_counts + 1e-6)
    pos_weight = pos_weight.to(device)
    logger.info(f"Class weights: {pos_weight.tolist()}")

    # Optimizer & scheduler
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)
    total_steps = len(train_loader) * args.epochs
    warmup_steps = int(total_steps * 0.06)
    scheduler = get_linear_schedule_with_warmup(optimizer, warmup_steps, total_steps)

    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)

    # Training loop
    best_macro_f1 = 0.0
    best_epoch = 0

    for epoch in range(args.epochs):
        model.train()
        total_loss = 0.0

        pbar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{args.epochs}")
        for batch in pbar:
            inputs = {k: v.to(device) for k, v in batch.items()
                      if k in ("input_ids", "attention_mask")}
            labels = batch["ekman_labels"].float().to(device)

            logits = model(**inputs).logits
            loss = criterion(logits, labels)

            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()

            total_loss += loss.item()
            pbar.set_postfix({"loss": f"{loss.item():.4f}"})

        avg_loss = total_loss / len(train_loader)
        logger.info(f"Epoch {epoch+1} - Avg train loss: {avg_loss:.4f}")

        # Validation
        model.eval()
        val_preds, val_labels = [], []
        val_loss = 0.0

        with torch.no_grad():
            for batch in tqdm(val_loader, desc="Validating"):
                inputs = {k: v.to(device) for k, v in batch.items()
                          if k in ("input_ids", "attention_mask")}
                labels = batch["ekman_labels"].float().to(device)

                logits = model(**inputs).logits
                val_loss += criterion(logits, labels).item()
                probs = torch.sigmoid(logits).cpu().numpy()
                val_preds.append(probs)
                val_labels.append(batch["ekman_labels"].numpy())

        val_preds = np.concatenate(val_preds)
        val_labels = np.concatenate(val_labels)
        val_avg_loss = val_loss / len(val_loader)

        metrics = compute_metrics(val_labels, val_preds, threshold=args.threshold)
        metrics["val_loss"] = val_avg_loss

        logger.info(f"Epoch {epoch+1} validation:")
        for k, v in metrics.items():
            logger.info(f"  {k}: {v:.4f}")

        if metrics["macro_f1"] > best_macro_f1:
            best_macro_f1 = metrics["macro_f1"]
            best_epoch = epoch + 1

    logger.info(f"Best macro F1: {best_macro_f1:.4f} at epoch {best_epoch}")

    # Temperature scaling
    temperature = find_temperature(model, val_loader, device)

    # Final test metrics
    logger.info("Evaluating on test set...")
    model.eval()
    test_preds, test_labels_list = [], []
    with torch.no_grad():
        for batch in tqdm(test_loader, desc="Testing"):
            inputs = {k: v.to(device) for k, v in batch.items()
                      if k in ("input_ids", "attention_mask")}
            logits = model(**inputs).logits
            probs = torch.sigmoid(logits / temperature).cpu().numpy()
            test_preds.append(probs)
            test_labels_list.append(batch["ekman_labels"].numpy())

    test_preds = np.concatenate(test_preds)
    test_labels_arr = np.concatenate(test_labels_list)
    test_metrics = compute_metrics(test_labels_arr, test_preds, threshold=args.threshold)

    logger.info("Test set results:")
    for k, v in test_metrics.items():
        logger.info(f"  {k}: {v:.4f}")

    # Save model
    logger.info(f"Saving model to {MODEL_PATH}...")
    MODEL_PATH.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(MODEL_PATH)
    tokenizer.save_pretrained(MODEL_PATH)
    torch.save({"temperature": temperature}, MODEL_PATH / "temperature.pt")

    # Save threshold and label info
    with open(MODEL_PATH / "inference_config.json", "w") as f:
        json.dump({
            "threshold": args.threshold,
            "temperature": temperature,
            "labels": _EKMAN_LABELS,
            "id2label": ID2LABEL,
            "label2id": LABEL2ID,
        }, f, indent=2)

    logger.info("Done! Model saved.")
    return test_metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train multi-label emotion classifier")
    parser.add_argument("--model_name", default="roberta-base",
                        help="Base HuggingFace model (default: roberta-base)")
    parser.add_argument("--epochs", type=int, default=5,
                        help="Number of training epochs (default: 5)")
    parser.add_argument("--batch_size", type=int, default=16,
                        help="Training batch size (default: 16)")
    parser.add_argument("--lr", type=float, default=2e-5,
                        help="Learning rate (default: 2e-5)")
    parser.add_argument("--threshold", type=float, default=0.3,
                        help="Sigmoid threshold for multi-label (default: 0.3)")
    parser.add_argument("--max_length", type=int, default=128,
                        help="Max token length (default: 128)")

    args = parser.parse_args()
    train(args)
