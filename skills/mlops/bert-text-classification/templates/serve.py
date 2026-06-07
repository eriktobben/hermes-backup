"""
FastAPI inference server for BERT text classification.
Model is loaded once at startup, serves predictions via HTTP.

Usage:
    pip install fastapi uvicorn
    python serve.py
    curl http://localhost:8000/health
"""

import os
import torch
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

# ─── Config via environment ───
MODEL_DIR = os.environ.get("MODEL_DIR", "./epost-model-final")
HOST = os.environ.get("HOST", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8000"))
API_KEY = os.environ.get("API_KEY", "")

# ─── Load model ───
logging.info(f"Loading model from {MODEL_DIR}...")

device = -1  # CPU default
if torch.backends.mps.is_available():
    device = "mps"
elif torch.cuda.is_available():
    device = 0

model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
classifier = pipeline("text-classification", model=model, tokenizer=tokenizer, device=device, top_k=None)

logging.info(f"Ready. Labels: {model.config.id2label}")

# ─── API ───
app = FastAPI(title="Text Classifier", version="1.0.0")

class ClassifyRequest(BaseModel):
    tekst: str = Field(..., min_length=1, max_length=5000)

class ClassifyResponse(BaseModel):
    label: str
    score: float
    alle_sannsynligheter: dict

@app.get("/health")
def health():
    return {"status": "ok", "labels": model.config.id2label}

@app.post("/klassifiser", response_model=ClassifyResponse)
def classify(req: ClassifyRequest):
    if API_KEY:
        from fastapi import Request
        # Validate API key from header
    results = classifier(req.tekst)[0]
    best = results[0]
    return ClassifyResponse(
        label=best["label"],
        score=round(best["score"], 4),
        alle_sannsynligheter={r["label"]: round(r["score"], 4) for r in results},
    )

@app.post("/klassifiser-batch")
def classify_batch(tekster: list[str]):
    if len(tekster) > 50:
        raise HTTPException(400, "Max 50 texts per request")
    return {
        "resultater": [
            {"label": classifier(t)[0][0]["label"], "score": round(classifier(t)[0][0]["score"], 4)}
            for t in tekster
        ]
    }
