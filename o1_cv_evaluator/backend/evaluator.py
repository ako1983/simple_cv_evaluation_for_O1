"""LLM routing layer.

Exposes a single async `evaluate()` entry point that dispatches the CV to one
of three providers (Claude, OpenAI, Gemini) and returns a validated
`EvaluationResult`. Each provider is instructed to emit the same JSON schema
so callers can rely on a uniform structure.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from typing import List, Optional

from .criteria import O1A_CRITERIA, criteria_block, criterion_names
from .schemas import (
    CriterionEvaluation,
    EvaluationResult,
    ModelChoice,
)

logger = logging.getLogger(__name__)

CLAUDE_MODEL = "claude-sonnet-4-20250514"
OPENAI_MODEL = "gpt-4o"
GEMINI_MODEL = "gemini-1.5-pro"

JSON_SCHEMA_DESCRIPTION = """\
Return ONLY a JSON object — no prose, no markdown fences — matching this schema:

{
  "overall_likelihood": "low" | "medium" | "high",
  "overall_summary": "2-4 sentence holistic judgment grounded in the evidence",
  "criteria": [
    {
      "name": "<one of the eight criterion names, verbatim>",
      "met": true | false,
      "confidence": "low" | "medium" | "high",
      "evidence": "specific quotes/paraphrases from the CV supporting the call; '' if none",
      "gaps": "what is missing or weak for this criterion; '' if fully met with high confidence"
    }
  ]
}

The `criteria` array MUST contain exactly one entry per criterion below, in the
order given, with `name` matching exactly.
"""


def _system_prompt() -> str:
    return (
        "You are an immigration analyst evaluating a CV against the USCIS O-1A "
        "extraordinary-ability criteria (8 CFR 214.2(o)(3)(iii)(B)). You are "
        "evidence-driven and conservative: only mark a criterion as `met` when "
        "the CV contains concrete, named evidence — not aspirational language. "
        "Distinguish 'met' (clear evidence) from 'high confidence' (you are sure "
        "of the call, whether positive or negative). A criterion can be `met: "
        "false` with `confidence: high` when the CV demonstrably lacks it. "
        "Overall likelihood reflects how plausibly the person would satisfy the "
        "three-criterion regulatory threshold."
    )


def _user_prompt(cv_text: str, rag_context: Optional[str]) -> str:
    parts = [
        "## O-1A Criteria",
        criteria_block(),
        "",
        "## Required output",
        JSON_SCHEMA_DESCRIPTION,
    ]
    if rag_context:
        parts += [
            "",
            "## USCIS guidance excerpts (retrieved)",
            "Use these to interpret the criteria. Cite the spirit of the guidance "
            "in your `evidence`/`gaps` fields when relevant, but do NOT fabricate "
            "CV content.",
            rag_context,
        ]
    parts += [
        "",
        "## CV under review",
        cv_text.strip(),
    ]
    return "\n".join(parts)


def _extract_json(raw: str) -> dict:
    """Best-effort JSON extraction — strips code fences and finds the outermost object."""
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"No JSON object found in model output: {raw[:300]}")
    return json.loads(text[start : end + 1])


def _normalize(raw_json: dict) -> EvaluationResult:
    """Validate and back-fill any missing criteria so downstream code can rely on completeness."""
    by_name = {c.get("name", "").strip().lower(): c for c in raw_json.get("criteria", [])}
    ordered: List[CriterionEvaluation] = []
    for spec in O1A_CRITERIA:
        match = by_name.get(spec["name"].lower())
        if match is None:
            ordered.append(
                CriterionEvaluation(
                    name=spec["name"],
                    met=False,
                    confidence="low",
                    evidence="",
                    gaps="Model did not return an assessment for this criterion.",
                )
            )
            continue
        ordered.append(
            CriterionEvaluation(
                name=spec["name"],
                met=bool(match.get("met", False)),
                confidence=match.get("confidence", "low"),
                evidence=match.get("evidence", "") or "",
                gaps=match.get("gaps", "") or "",
            )
        )
    return EvaluationResult(
        overall_likelihood=raw_json.get("overall_likelihood", "low"),
        overall_summary=raw_json.get("overall_summary", "").strip(),
        criteria=ordered,
    )


async def _call_claude(system: str, user: str) -> str:
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    msg = await client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=2048,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(block.text for block in msg.content if getattr(block, "type", None) == "text")


async def _call_openai(system: str, user: str) -> str:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
    resp = await client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        response_format={"type": "json_object"},
        max_tokens=2048,
    )
    return resp.choices[0].message.content or ""


async def _call_gemini(system: str, user: str) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    config = types.GenerateContentConfig(
        system_instruction=system,
        response_mime_type="application/json",
        max_output_tokens=2048,
    )

    def _sync_call() -> str:
        resp = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=user,
            config=config,
        )
        return resp.text or ""

    return await asyncio.to_thread(_sync_call)


_ROUTES = {
    "claude": (_call_claude, CLAUDE_MODEL),
    "openai": (_call_openai, OPENAI_MODEL),
    "gemini": (_call_gemini, GEMINI_MODEL),
}


def model_id_for(choice: ModelChoice) -> str:
    return _ROUTES[choice][1]


def available_providers() -> dict:
    return {
        "claude": bool(os.environ.get("ANTHROPIC_API_KEY")),
        "openai": bool(os.environ.get("OPENAI_API_KEY")),
        "gemini": bool(os.environ.get("GEMINI_API_KEY")),
    }


async def evaluate(
    cv_text: str,
    model: ModelChoice = "claude",
    rag_context: Optional[str] = None,
) -> EvaluationResult:
    """Route the CV to the requested provider and return a structured evaluation."""
    if model not in _ROUTES:
        raise ValueError(f"Unsupported model: {model}. Choose one of {list(_ROUTES)}.")

    caller, model_id = _ROUTES[model]
    system = _system_prompt()
    user = _user_prompt(cv_text, rag_context)

    logger.info("Calling %s (%s) — rag=%s", model, model_id, bool(rag_context))
    raw = await caller(system, user)
    raw_json = _extract_json(raw)
    return _normalize(raw_json)


# Keep linter quiet about unused import in the public surface
__all__ = [
    "evaluate",
    "available_providers",
    "model_id_for",
    "criterion_names",
]
