"""Pydantic models for request/response payloads shared by the API and LLMs."""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field

Confidence = Literal["low", "medium", "high"]
Likelihood = Literal["low", "medium", "high"]
ModelChoice = Literal["claude", "openai", "gemini"]


class CriterionEvaluation(BaseModel):
    name: str
    met: bool
    confidence: Confidence
    evidence: str
    gaps: str


class EvaluationResult(BaseModel):
    overall_likelihood: Likelihood
    overall_summary: str
    criteria: List[CriterionEvaluation]


class EvaluateRequest(BaseModel):
    cv_text: str = Field(..., min_length=10, description="Plain-text CV content.")
    model: ModelChoice = Field("claude", description="LLM provider to route the request to.")
    use_rag: bool = Field(False, description="If true, augment the prompt with USCIS legal context.")


class EvaluateResponse(EvaluationResult):
    model_used: str
    rag_used: bool
    retrieved_chunks: Optional[int] = None


class IngestResponse(BaseModel):
    files_processed: int
    chunks_added: int
    message: str


class HealthResponse(BaseModel):
    status: str
    providers: dict
