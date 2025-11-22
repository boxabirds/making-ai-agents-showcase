import os
from typing import List

from openai import OpenAI

from .models import SummaryOutput

REPORT_SYSTEM_PROMPT = (
    "You are a meticulous technical writer. Follow the user prompt exactly, regardless of topic. "
    "Use only the provided evidence. Every paragraph or bullet must include at least one citation "
    "from the allowed list, in the format path:start-end. Do not invent citations or content."
)


def _client():
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY not set; cannot call LLM.")
    return OpenAI(api_key=key)


def summarize_text(text: str, instructions: str = "") -> SummaryOutput:
    """
    Summarize text using OpenAI.
    """
    client = _client()
    prompt = f"{instructions}\n\n{text[:6000]}"
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    content = resp.choices[0].message.content
    return SummaryOutput(text=content or "", citations=[], confidence=0.7)


def draft_report(prompt: str, evidences: List[str]) -> str:
    """
    Draft report using OpenAI.
    """
    if not evidences:
        raise RuntimeError("No evidence provided to draft report.")
    client = _client()
    evidence_text = "\n".join(evidences)
    user_content = "\n".join(
        [
            f"User prompt:\n{prompt}",
            "",
            "Evidence (use these citations as-is; do not invent new ones):",
            evidence_text,
            "",
            "Instructions:",
            "- Satisfy the user prompt precisely; do not add template sections unless requested.",
            "- Every paragraph or bullet must include at least one citation drawn from the evidence list.",
            "- Do not emit citations that are not present in the evidence.",
        ]
    )
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": REPORT_SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0,
    )
    return resp.choices[0].message.content or ""
