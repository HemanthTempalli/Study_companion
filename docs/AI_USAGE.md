# AI Usage Documentation

## Models Used

| Feature | Model | Provider |
|---------|-------|----------|
| AI Tutor | llama-3.1-70b-versatile | Groq |
| Quiz Generation | llama-3.1-70b-versatile | Groq |
| Quiz Evaluation | llama-3.1-70b-versatile | Groq |
| Concept Extraction | llama-3.1-70b-versatile | Groq |
| Recommendations | llama-3.1-70b-versatile | Groq |
| Embeddings | all-MiniLM-L6-v2 | sentence-transformers (local) |

## Per-Feature AI Usage

### AI Tutor (RAG)
- **Input**: User question + retrieved document chunks (context)
- **Output**: Grounded answer with citation metadata
- **Avg tokens**: ~2000 input, ~500 output
- **Latency**: ~800ms

### Quiz Generation
- **Input**: Document chunks + mastery data + difficulty calibration
- **Output**: Structured JSON with questions, options, correct answers
- **Avg tokens**: ~3000 input, ~1500 output
- **Latency**: ~1500ms

### Quiz Evaluation (Open-Ended)
- **Input**: Question + correct answer + student answer
- **Output**: Score (0-100) + detailed feedback JSON
- **Avg tokens**: ~800 input, ~400 output
- **Latency**: ~500ms

### Concept Extraction
- **Input**: First 10 pages of uploaded material (sampled)
- **Output**: 5-15 concept names with descriptions
- **Avg tokens**: ~2000 input, ~800 output
- **Latency**: ~1000ms

### Recommendations
- **Input**: Mastery data + quiz history + available materials
- **Output**: Single actionable recommendation with reasoning
- **Avg tokens**: ~1000 input, ~300 output
- **Latency**: ~500ms

## Cost Tracking

Every AI call is logged to `ai_usage_logs` with estimated costs:

```
Groq (llama-3.1-70b):
  Input: $0.59 / 1M tokens
  Output: $0.79 / 1M tokens
```

Estimated cost per session (upload + 5 tutor questions + 1 quiz):
- **~$0.005** (half a cent)

## Observability

Admin dashboard shows:
- Total AI requests per feature
- Average latency per feature
- Token usage breakdown
- Error rates and failure messages
- Cost estimates over time

## Hallucination Prevention

1. **RAG Grounding**: Tutor answers are grounded in retrieved document chunks
2. **Citation Requirements**: System prompt requires citations for all claims
3. **Insufficient Evidence Detection**: When similarity scores are too low, the system flags it
4. **Structured Output**: JSON schemas prevent free-form hallucination
5. **Retry Logic**: If JSON parsing fails, a stricter prompt is used on retry
