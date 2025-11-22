import os
from typing import List

from openai import OpenAI

from .models import SummaryOutput

REPORT_SYSTEM_PROMPT = (
    "Write a concise technical report. Every claim or paragraph must include a citation in the format path:start-end. "
    "Do not invent citations; only cite evidence you have."
)


def _client():
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY not set; cannot call LLM.")
    return OpenAI(api_key=key)


def summarize_text(text: str, instructions: str = "") -> SummaryOutput:
    """
    Summarize text using OpenAI. Raises if no API key is available.
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


def draft_report(prompt: str, summaries: List[str]) -> str:
    """
    Draft report using OpenAI. Raises if no API key is available.
    """
    client = _client()
    content = "\n\n".join(["Summaries:"] + summaries)
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": REPORT_SYSTEM_PROMPT},
            {"role": "user", "content": f"{prompt}\n\n{content}"},
        ],
        temperature=0,
    )
    return resp.choices[0].message.content or ""
