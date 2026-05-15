"""FastAPI application exposing /evaluate, /ingest, and /health."""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .evaluator import available_providers, evaluate, model_id_for
from .rag import collection_size, ingest_legal_docs, num_retrieved, retrieve_context
from .schemas import (
    EvaluateRequest,
    EvaluateResponse,
    HealthResponse,
    IngestResponse,
)

load_dotenv()

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("o1_cv_evaluator")

app = FastAPI(
    title="O-1A CV Evaluator",
    description="Evidence-driven evaluation of CVs against USCIS O-1A criteria.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        providers={
            **available_providers(),
            "rag_chunks_indexed": collection_size(),
        },
    )


@app.post("/ingest", response_model=IngestResponse)
async def ingest() -> IngestResponse:
    try:
        files, chunks = ingest_legal_docs()
    except Exception as exc:
        logger.exception("Ingestion failed")
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {exc}") from exc
    if files == 0:
        return IngestResponse(
            files_processed=0,
            chunks_added=0,
            message=(
                "No PDFs found under data/legal_docs/. Drop USCIS guidance PDFs "
                "in that folder and call /ingest again."
            ),
        )
    return IngestResponse(
        files_processed=files,
        chunks_added=chunks,
        message=(
            f"Ingested {chunks} new chunks from {files} PDFs. "
            f"Collection now holds {collection_size()} chunks."
        ),
    )


@app.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_cv(req: EvaluateRequest) -> EvaluateResponse:
    providers = available_providers()
    if not providers.get(req.model):
        raise HTTPException(
            status_code=400,
            detail=(
                f"Provider '{req.model}' is not configured. "
                f"Set the corresponding API key in your .env."
            ),
        )

    rag_context = None
    if req.use_rag:
        try:
            rag_context = retrieve_context(req.cv_text, k=5)
        except Exception as exc:
            logger.warning("RAG retrieval failed, falling back to no-RAG: %s", exc)
            rag_context = None

    try:
        result = await evaluate(req.cv_text, model=req.model, rag_context=rag_context)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=f"Missing API key: {exc}") from exc
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=f"Model output invalid: {exc}") from exc
    except Exception as exc:
        logger.exception("LLM evaluation failed")
        raise HTTPException(status_code=502, detail=f"Evaluation failed: {exc}") from exc

    return EvaluateResponse(
        **result.model_dump(),
        model_used=model_id_for(req.model),
        rag_used=bool(rag_context),
        retrieved_chunks=num_retrieved(rag_context) if rag_context else 0,
    )


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
