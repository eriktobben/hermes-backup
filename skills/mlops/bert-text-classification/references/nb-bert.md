# Norwegian BERT Models (nb-bert)

## NbAiLab/nb-bert-base

The go-to BERT model for Norwegian text classification.

- **Size:** ~110 MB (PyTorch), ~200 MB loaded
- **Tokenization:** SentencePiece BPE, case-sensitive, preserves æøåÆØÅ
- **Context length:** 512 tokens (plenty for emails)
- **Training data:** Norwegian Wikipedia, news articles, government documents
- **License:** MIT

### Performance

| Task | CPU (2 vCPU) | MacBook Air M2 | GPU |
|---|---|---|---|
| Training (100 examples, 5 epochs) | ~3 min | ~1.5 min | ~20 s |
| Inference (single text) | ~50 ms | ~30 ms | ~10 ms |
| Batch inference (50 texts) | ~200 ms | ~100 ms | ~50 ms |

### Known limitations

- **Tokenizes æøå correctly** but doesn't understand English well. Mixing Norwegian + English in training data is fine, but 100% English text will perform worse than distilbert.
- **BERT-base** not distilled — slower than distilbert but better quality.

## Alternatives

| Model | Size | Notes |
|---|---|---|
| NbAiLab/nb-bert-small | ~50 MB | Faster, slightly worse quality |
| NbAiLab/nb-bert-base-community | ~110 MB | Community-trained, different data mix |
| NbAiLab/nb-roberta-base | ~200 MB | RoBERTa architecture, better on some benchmarks |
| NbAiLab/nb-electra-base | ~110 MB | ELECTRA, faster training |
| NbAiLab/nb-bert-base-128 | ~110 MB | 128K vocab variant, experimental |

## When to choose nb-bert vs alternatives

- **nb-bert-base:** Norwegian emails, documents, support tickets → **pick this**
- **distilbert-base-uncased:** English text, max speed needed
- **bert-base-multilingual-cased:** Mix of Norwegian, English, and other European languages
- **nb-bert-small:** Very constrained CPU/memory budget (<1 GB RAM available)
