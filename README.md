# AI Memory Doctor (Personal Cognitive Assistant)

AI Memory Doctor is a hybrid memory system that captures, structures, stores, retrieves, summarizes, and analyzes personal memory data.

## Implemented Core Capabilities

- Memory input and structuring from natural language
- ML-based memory type categorization (activity, decision, idea, mistake, event)
- Hybrid storage:
  - Structured SQL storage for exact filtering
  - FAISS vector indexing for semantic retrieval
- Hybrid retrieval (temporal filters + semantic similarity + ranking)
- Temporal reasoning (today, yesterday, this week, last week, this month, last month, morning, afternoon, evening, night)
- Memory update and correction with history/version tracking
- Summarization for daily/weekly/monthly windows
- Insight and pattern analysis
- Free-form memory search
- User control (view, edit, delete)
- Evaluation metrics endpoints

## Project Structure

- backend/app/api: HTTP endpoints
- backend/app/services: business and AI logic
- backend/app/models: database models
- backend/app/db: SQLAlchemy database setup
- docs/backend/features: feature-specific technical READMEs

## Environment Setup

1. Create and activate Python environment.
2. Install dependencies.
3. Configure environment variables from .env.example.
4. Start API server.

### Example Commands

```bash
cd backend
pip install -r ../requirements.txt
copy ../.env.example .env
uvicorn app.main:app --reload
```

## Required and Optional API Keys

Current implementation works without external LLM keys.

- For deterministic local mode:
  - Set LLM_PROVIDER=none
- For future external LLM mode:
  - Set LLM_PROVIDER to your provider name
  - Set LLM_API_KEY with your real key
  - Keep LLM_MODEL as your chosen model

If you share your preferred provider key, provider integration can be added in:

- backend/app/services/llm_service.py

## Main Endpoints

### Auth

- POST /auth/register
- POST /auth/login

### Memory Write and Manage

- POST /add-memory
- GET /memories
- PUT /memories/{memory_id}
- DELETE /memories/{memory_id}
- POST /update-memory (natural language correction)
- GET /memories/{memory_id}/history

### Retrieval and Intelligence

- POST /search-memory
- POST /summarize
- GET /insights
- POST /agent

### Evaluation

- GET /evaluation/metrics
- POST /evaluation/metrics
- POST /evaluation/export-report

Single-command thesis export:

```bash
curl -X POST http://127.0.0.1:8000/evaluation/export-report \\
  -H "Authorization: Bearer <TOKEN>" \\
  -H "Content-Type: application/json" \\
  -d '{"report_name":"thesis_eval"}'
```

Generated files are saved under backend/reports as both JSON and CSV.

## Feature Documentation

Read detailed design and usage in docs/backend/features.

- memory-input.md
- memory-storage.md
- retrieval-and-search.md
- temporal-reasoning.md
- update-and-versioning.md
- summarization.md
- insights.md
- user-control.md
- evaluation.md
- agent-orchestration.md
- auth-security.md

Deployment checklist:

- docs/backend/deployment-readiness.md

## Notes

- Voice input is out of scope for current backend and remains future work.
- External integrations (calendar, email, messaging) are out of scope for current phase.
- Current system is optimized for academic/single-user or lightweight multi-user usage.

## Continuous Learning (Optional)

- The current system uses a static trained classification model (ML classifier trained on labeled dataset).
- The system currently uses a pre-trained classification model and does not automatically update itself with new user data. However, it is designed to support future extension for continuous learning.
- No automatic retraining is triggered during runtime in this version.
- A future extension placeholder exists in [backend/app/services/ml_classifier_service.py](backend/app/services/ml_classifier_service.py).
