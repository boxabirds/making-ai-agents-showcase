"""
DSPy-based modules for summarization and drafting.

These modules wrap our LLM helper functions to keep DSPy in the loop for
orchestration while enforcing citation-aware outputs.
"""

import dspy

from .llm import summarize_text, draft_report


class SummarizeFileModule(dspy.Module):
    def forward(self, file_path: str, content: str):
        summary = summarize_text(content, instructions=f"Summarize file {file_path} with citations if possible.")
        # Return a dict to keep it flexible for downstream use
        return {"text": summary.text, "confidence": summary.confidence, "citations": summary.citations}


class SummarizeModuleModule(dspy.Module):
    def forward(self, module_path: str, child_summaries: list[str]):
        # Simple aggregation; an LM could refine this when available
        text = f"Module: {module_path}\n" + "\n".join(child_summaries)
        return {"text": text, "confidence": 0.5, "citations": []}


class DraftModule(dspy.Module):
    def forward(self, prompt: str, evidences: list[str]):
        report = draft_report(prompt, evidences)
        return {"text": report}
