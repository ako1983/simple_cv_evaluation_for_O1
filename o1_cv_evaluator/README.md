# O-1A CV Evaluator

Evidence-driven, per-criterion evaluation of a CV against the eight USCIS
O-1A extraordinary-ability criteria (8 CFR 214.2(o)(3)(iii)(B)).

- **Backend** — FastAPI service with three endpoints (`/evaluate`, `/ingest`,
  `/health`), routing CVs to Claude (default), GPT-4o, or Gemini 1.5 Pro and
  returning a structured per-criterion JSON report.
- **Frontend** — Streamlit app for uploading a PDF CV (or pasting text), picking
  a model, toggling RAG, and reading a card-per-criterion report with
  evidence, confidence, and gap analysis.
- **RAG** — Local ChromaDB persistence over USCIS guidance PDFs dropped in
  `data/legal_docs/`. When RAG is off, the evaluator uses only the eight
  hardcoded criteria; when on, retrieved excerpts are appended to the prompt.

## Layout

```
o1_cv_evaluator/
├── backend/
│   ├── main.py          # FastAPI app + endpoints
│   ├── evaluator.py     # LLM routing (Claude / OpenAI / Gemini)
│   ├── rag.py           # ChromaDB ingestion + retrieval
│   ├── criteria.py      # 8 USCIS O-1A criteria
│   └── schemas.py       # Pydantic request/response models
├── frontend/
│   └── streamlit_app.py # UI
├── data/
│   ├── legal_docs/      # Drop USCIS PDFs here, then POST /ingest
│   └── chroma/          # Chroma persistent store (auto-created)
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

```bash
cd o1_cv_evaluator
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                # then fill in at least one API key
```

You need at least one provider key. Claude is the default in both the API
and the UI, so `ANTHROPIC_API_KEY` is the recommended starting point.

## Run

In one terminal, start the backend:

```bash
uvicorn backend.main:app --reload --port 8000
```

In a second terminal, start the UI:

```bash
streamlit run frontend/streamlit_app.py
```

The Streamlit app talks to the backend at `BACKEND_URL` (defaults to
`http://localhost:8000`).

## Ingesting legal docs for RAG

1. Drop USCIS guidance PDFs into `data/legal_docs/` (e.g. Chapter 2/4/7 of the
   USCIS Policy Manual on O-1 classification).
2. Trigger ingestion either way:
   ```bash
   curl -X POST http://localhost:8000/ingest
   # or, without the server:
   python -m backend.rag
   ```
3. Toggle **Use RAG** in the Streamlit sidebar.

Chunks are deduplicated by content hash, so re-running `/ingest` after adding
new PDFs is safe.

## API

### `GET /health`

```json
{
  "status": "ok",
  "providers": {
    "claude": true,
    "openai": false,
    "gemini": false,
    "rag_chunks_indexed": 0
  }
}
```

### `POST /ingest`

No body. Reads every PDF under `data/legal_docs/`, chunks them, and upserts
into Chroma.

### `POST /evaluate`

Request:
```json
{
  "cv_text": "...",
  "model": "claude",       // "claude" | "openai" | "gemini"
  "use_rag": false
}
```

Response (every provider returns the same shape):
```json
{
  "overall_likelihood": "medium",
  "overall_summary": "...",
  "criteria": [
    {
      "name": "Awards",
      "met": true,
      "confidence": "high",
      "evidence": "...",
      "gaps": ""
    }
    // ... one entry per criterion, in the order defined in criteria.py
  ],
  "model_used": "claude-sonnet-4-20250514",
  "rag_used": false,
  "retrieved_chunks": 0
}
```

## Design notes

- **Conservative evaluation.** The system prompt instructs the model to mark a
  criterion as `met` only when concrete, named evidence appears in the CV. A
  criterion can be `met: false` with `confidence: high` when the CV
  demonstrably lacks it — confidence is about certainty of the call, not the
  positivity of it.
- **Schema normalization.** The evaluator validates and back-fills the model
  output, so the frontend can always render eight cards in a fixed order even
  if a provider drops one.
- **No vendor lock-in for embeddings.** RAG uses Chroma's built-in default
  embedding so the project runs offline-ish without extra keys for retrieval.
