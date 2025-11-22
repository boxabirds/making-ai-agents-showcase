from datetime import datetime, timezone
from typing import List, Tuple

from .citations import generate_citation_from_chunk, validate_citation
from .dspy_pipeline import SummarizeFileModule, SummarizeModuleModule
from .models import SummaryRecord
from .store import Store


def summarize_file(store: Store, file_id: int) -> SummaryRecord:
    """
    Summarize a file using DSPy module (LLM-backed if available; deterministic if ALLOW_DETERMINISTIC_FALLBACKS=1).
    """
    file_rec = store.get_file_by_id(file_id)
    if not file_rec:
        raise ValueError(f"file_id {file_id} not found")
    chunks = store.get_chunks_for_file(file_id)
    joined = "\n".join(chunk.text for chunk in chunks)
    summ_module = SummarizeFileModule()
    result = summ_module(file_path=file_rec.path, content=joined)
    text = " ".join(result["text"].split())
    confidence = float(result.get("confidence", 0.5))
    # attach at least one citation to enforce grounding
    citation_suffix = ""
    if chunks:
        first_chunk = chunks[0]
        citation_suffix = f" [{generate_citation_from_chunk(first_chunk, file_rec.path)}]"
    summary = SummaryRecord(
        level="file",
        target_id=file_id,
        text=text + citation_suffix,
        confidence=confidence,
        created_at=datetime.now(timezone.utc),
    )
    summary_id = store.add_summary(summary)
    summary.id = summary_id
    return summary


def summarize_all_files(store: Store) -> List[SummaryRecord]:
    summaries: List[SummaryRecord] = []
    for file_rec in store.get_all_files():
        summaries.append(summarize_file(store, file_rec.id))  # type: ignore
    return summaries


def summarize_module(store: Store, module_path: str, file_summaries: List[SummaryRecord]) -> SummaryRecord:
    """
    Aggregate file summaries into a module-level summary using DSPy reduce module.
    """
    reduce_module = SummarizeModuleModule()
    result = reduce_module(module_path=module_path, child_summaries=[s.text for s in file_summaries])
    # gather citations from children
    child_citations = []
    for s in file_summaries:
        for token in s.text.split():
            if token.startswith("[") and token.endswith("]"):
                try:
                    validate_citation(token.strip("[]"))
                    child_citations.append(token.strip("[]"))
                except Exception:
                    continue
    citation_suffix = ""
    if child_citations:
        # include first valid citation to ground module summary
        citation_suffix = f" [{child_citations[0]}]"
    summary = SummaryRecord(
        level="module",
        target_id=-1,  # module identifier can be modeled separately if desired
        text=" ".join(result["text"].split()) + citation_suffix,
        confidence=float(result.get("confidence", 0.5)),
        created_at=datetime.now(timezone.utc),
    )
    summary_id = store.add_summary(summary)
    summary.id = summary_id
    return summary
