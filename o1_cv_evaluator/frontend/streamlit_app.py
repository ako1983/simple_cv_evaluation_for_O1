"""Streamlit UI for the O-1A CV evaluator.

Run:
    streamlit run frontend/streamlit_app.py

The UI calls into the FastAPI backend at $BACKEND_URL (defaults to
http://localhost:8000).
"""

from __future__ import annotations

import io
import os
from typing import Optional

import httpx
import streamlit as st
from pypdf import PdfReader

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")
REQUEST_TIMEOUT = 120.0

MODEL_OPTIONS = {
    "Claude Sonnet 4 (default)": "claude",
    "GPT-4o": "openai",
    "Gemini 1.5 Pro": "gemini",
}

LIKELIHOOD_BADGES = {
    "high": ("High", "#1b873f"),
    "medium": ("Medium", "#b8860b"),
    "low": ("Low", "#a53030"),
}

CONFIDENCE_BADGES = {
    "high": "🟢 high confidence",
    "medium": "🟡 medium confidence",
    "low": "🔴 low confidence",
}


def extract_pdf_text(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    pages = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n".join(pages).strip()


def call_evaluate(cv_text: str, model: str, use_rag: bool) -> dict:
    with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
        resp = client.post(
            f"{BACKEND_URL}/evaluate",
            json={"cv_text": cv_text, "model": model, "use_rag": use_rag},
        )
    if resp.status_code >= 400:
        detail: str
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        raise RuntimeError(f"Backend error {resp.status_code}: {detail}")
    return resp.json()


def call_health() -> Optional[dict]:
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{BACKEND_URL}/health")
        if resp.status_code == 200:
            return resp.json()
    except httpx.HTTPError:
        return None
    return None


def render_likelihood(level: str, summary: str) -> None:
    label, color = LIKELIHOOD_BADGES.get(level, ("Unknown", "#444"))
    st.markdown(
        f"""
        <div style="padding:1rem 1.25rem;border-radius:10px;background:{color};color:white;">
          <div style="font-size:0.85rem;text-transform:uppercase;letter-spacing:0.08em;opacity:0.85;">
            Overall qualification likelihood
          </div>
          <div style="font-size:2rem;font-weight:700;margin-top:0.15rem;">{label}</div>
          <div style="margin-top:0.4rem;font-size:0.95rem;line-height:1.4;">{summary}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_criterion_card(crit: dict) -> None:
    name = crit.get("name", "Unknown")
    met = bool(crit.get("met"))
    confidence = crit.get("confidence", "low")
    icon = "✅" if met else "❌"
    header = f"{icon}  {name}  —  {CONFIDENCE_BADGES.get(confidence, confidence)}"
    with st.expander(header, expanded=False):
        st.markdown("**Evidence found**")
        st.write(crit.get("evidence") or "_No supporting evidence identified in the CV._")
        st.markdown("**Gap analysis**")
        st.write(crit.get("gaps") or "_No gaps identified — criterion is solidly met._")


def main() -> None:
    st.set_page_config(page_title="O-1A CV Evaluator", page_icon="🛂", layout="wide")
    st.title("O-1A CV Evaluator")
    st.caption(
        "Evidence-driven, per-criterion analysis of a CV against the USCIS "
        "O-1A extraordinary-ability criteria."
    )

    with st.sidebar:
        st.header("Settings")
        model_label = st.selectbox(
            "LLM",
            list(MODEL_OPTIONS.keys()),
            index=0,
            help="Claude Sonnet 4 is the default. Switch to compare model judgments.",
        )
        model_key = MODEL_OPTIONS[model_label]
        use_rag = st.checkbox(
            "Use RAG (USCIS guidance)",
            value=False,
            help=(
                "When enabled, retrieved excerpts from ingested USCIS guidance "
                "are appended to the prompt. Ingest PDFs via the backend "
                "/ingest endpoint first."
            ),
        )

        st.divider()
        st.subheader("Backend")
        st.code(BACKEND_URL, language="bash")
        health = call_health()
        if health is None:
            st.error("Backend unreachable")
        else:
            providers = health.get("providers", {})
            for key in ("claude", "openai", "gemini"):
                ok = providers.get(key)
                st.write(("✅ " if ok else "⚠️ ") + key + (" configured" if ok else " missing key"))
            st.caption(f"RAG chunks indexed: {providers.get('rag_chunks_indexed', 0)}")

    st.subheader("CV input")
    tab_upload, tab_paste = st.tabs(["Upload PDF", "Paste text"])
    cv_text = ""
    with tab_upload:
        uploaded = st.file_uploader("Upload a CV (PDF)", type=["pdf"], accept_multiple_files=False)
        if uploaded is not None:
            with st.spinner("Extracting text from PDF…"):
                try:
                    cv_text = extract_pdf_text(uploaded.read())
                except Exception as exc:
                    st.error(f"Could not parse PDF: {exc}")
                    cv_text = ""
            if cv_text:
                st.success(f"Extracted {len(cv_text):,} characters")
                with st.expander("Preview extracted text"):
                    st.text(cv_text[:4000] + ("…" if len(cv_text) > 4000 else ""))

    with tab_paste:
        pasted = st.text_area("Paste CV text", height=300, placeholder="Paste full CV text here…")
        if pasted.strip() and not cv_text:
            cv_text = pasted.strip()

    run = st.button("Evaluate CV", type="primary", disabled=not cv_text.strip())

    if run and cv_text.strip():
        with st.spinner(f"Evaluating with {model_label}{' + RAG' if use_rag else ''}…"):
            try:
                result = call_evaluate(cv_text, model_key, use_rag)
            except Exception as exc:
                st.error(str(exc))
                return

        st.divider()
        render_likelihood(
            result.get("overall_likelihood", "low"),
            result.get("overall_summary", ""),
        )

        meta_cols = st.columns(3)
        meta_cols[0].metric("Model", result.get("model_used", "—"))
        meta_cols[1].metric("RAG", "on" if result.get("rag_used") else "off")
        meta_cols[2].metric("Retrieved chunks", result.get("retrieved_chunks") or 0)

        st.subheader("Per-criterion breakdown")
        criteria = result.get("criteria", [])
        met_count = sum(1 for c in criteria if c.get("met"))
        st.caption(
            f"Criteria met: {met_count} of {len(criteria)}  "
            f"(USCIS requires at least 3 to qualify under O-1A)."
        )
        for crit in criteria:
            render_criterion_card(crit)

        with st.expander("Raw JSON response"):
            st.json(result)


if __name__ == "__main__":
    main()
