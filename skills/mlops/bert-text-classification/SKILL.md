---
name: bert-text-classification
description: "Fine-tune BERT encoder models for text classification (spam detection, email routing, intent classification). Covers full lifecycle: data prep → training → FastAPI microservice → Laravel/backend integration."
version: 1.0.0
author: Hermes
license: MIT
dependencies: [transformers>=4.30.0, torch, datasets, scikit-learn, pandas, fastapi, uvicorn]
metadata:
  hermes:
    tags: [bert, classification, text-classification, fine-tuning, nb-bert, norwegian, fastapi, laravel, deployment, supervisor]
---

# BERT Text Classification

Fine-tune small encoder-only transformer models (BERT, DistilBERT, RoBERTa, etc.) for text classification tasks — spam detection, email routing, intent classification, sentiment analysis, content tagging.

## Why BERT over an LLM for classification

| Aspect | BERT encoder | LLM (generative) |
|---|---|---|
| Model size | 85–180 MB | 1–8 GB (quantized) |
| Inference speed | ~50 ms (CPU) | ~500 ms–2 s (CPU) |
| Accuracy on classification | Excellent | Good, but overkill |
| Training data needed | 50–200 per class | 100–1000+ |
| MacBook Air M2 | 20–50 eposter/sek | 2–5 sek per epost |

**Rule of thumb:** For any task that outputs a single label from a fixed set (spam/not-spam, kategori A/B/C), BERT is the right tool. Reach for an LLM only when you need free-text reasoning or multi-label with complex dependencies.

## Quick start

### 1. Choose a model

```python
# Norsk (anbefalt for norske eposter)
MODEL_NAME = "NbAiLab/nb-bert-base"     # ~110 MB

# Engelsk (raskest, minst)
MODEL_NAME = "distilbert-base-uncased"  # ~85 MB

# Flerspråklig
MODEL_NAME = "bert-base-multilingual-cased"  # ~180 MB
```

### 2. Prepare data

```python
data = {
    "text": ["eposttekst 1", "eposttekst 2", ...],
    "label": ["kategori_a", "kategori_b", ...],
}
```

Minimum **50–100 eksempler per klasse**.

### 3. Fine-tune

See `templates/train.py` for a complete training script.

Key transformers v5 API differences from older versions:

| Old (v4) | New (v5) |
|---|---|
| `tokenizer=tokenizer` (Trainer arg) | `processing_class=tokenizer` |
| `label_id` column name | `labels` column name |
| `Trainer(tokenizer=...)` | `Trainer(processing_class=...)` |

### 4. Deploy as FastAPI microservice

```bash
python serve.py
# Lytter på http://localhost:8000
```

See `templates/serve.py` for the server template.

### 5. Integrate with Laravel

See `references/laravel-integration.md` for the controller, routes, and config.

### 6. Process management (Supervisor)

See `templates/supervisor.conf` — drop into `/etc/supervisor/conf.d/` on a Forge server.

## Model selection guide

| Use case | Model | Size | MSG | Notes |
|---|---|---|---|---|
| Norske eposter | NbAiLab/nb-bert-base | 110 MB | 20/s | 🇳🇴 Best for norsk tekst |
| Engelsk, trenger fart | distilbert-base-uncased | 85 MB | 30/s | Raskest, minst |
| Flere språk | bert-base-multilingual-cased | 180 MB | 15/s | 100+ språk |
| Norsk, eksperimentell | NbAiLab/nb-bert-small | 50 MB | 40/s | Mindre, raskere |

## Deployment architecture (Laravel + Python microservice)

```
Email client → Laravel API (/api/epost/klassifiser) 
              → HTTP → FastAPI microservice (:8000)
              → nb-bert → "må_svare" (87%)
              → JSON response → Laravel → client
```

## Training tips

- **Balanced dataset:** Roughly equal examples per class prevents bias
- **Real data > synthetic:** Label real emails from your inbox
- **More data = better accuracy:** 50/class → ~80%, 200/class → ~90%+
- **Early stopping:** Monitor eval loss; stop when it plateaus
- **Augment with synonyms** if data is scarce

## Pitfalls

- **distilbert-base-uncased is English-only** — don't use for Norwegian text. The tokenizer strips æøå and lowercases everything. Use nb-bert-base instead.
- **transformers v5 API changes** caught many users — `tokenizer` renamed to `processing_class` in Trainer, `label_id` must be `labels` in dataset. Check version with `transformers.__version__`.
- **Training on CPU is slow for BERT-base** (~3s/step on 100 examples). For 500+ examples consider a GPU (RunPod ~$0.50/hr) or use distilbert.
- **Model memory on server:** ~300 MB RAM per model instance. Factor this into server sizing (2 vCPU/4 GB is fine for 1 model).
- **ONNX export** is possible but not necessary — PyTorch inference is fast enough on CPU for this use case.

## References

- `references/laravel-integration.md` — Laravel controller, routes, config, .env setup
- `references/nb-bert.md` — Norwegian BERT model details and alternatives

## Templates

- `templates/train.py` — Complete training script with data prep, tokenization, training loop, evaluation
- `templates/serve.py` — FastAPI microservice with health check, classify, batch endpoints
- `templates/supervisor.conf` — Supervisor config for Forge/Linux servers

## Scripts

- (none yet)
