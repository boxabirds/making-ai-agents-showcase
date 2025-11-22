from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

from .citations import generate_citation_from_chunk, validate_citation
from .dspy_pipeline import SummarizeFileModule, SummarizeModuleModule
from .models import SummaryRecord, ChunkRecord
from .store import Store
from .validation import validate_summary


def summarize_file(store: Store, file_id: int) -> SummaryRecord:
    """
    Summarize a file using the DSPy module (LLM-backed, no deterministic fallbacks in production).
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
    validate_summary(store, summary)
    return summary


def summarize_all_files(store: Store) -> List[SummaryRecord]:
    summaries: List[SummaryRecord] = []
    for file_rec in store.get_all_files():
        if not file_rec.parsed:
            continue
        summaries.append(summarize_file(store, file_rec.id))  # type: ignore
    return summaries


def summarize_project(store: Store, root_path: str) -> tuple[list[SummaryRecord], list[SummaryRecord], SummaryRecord, SummaryRecord]:
    chunk_summaries: List[SummaryRecord] = []
    file_summaries: List[SummaryRecord] = []
    package_id = store.add_package(root_path, Path(root_path).name)
    for file_rec in store.get_all_files():
        if not file_rec.parsed:
            continue
        chunk_summaries.extend(summarize_chunks(store, file_rec.id))  # type: ignore
        file_summaries.append(summarize_file(store, file_rec.id))  # type: ignore
    module_summary = summarize_module(store, module_path=root_path, file_summaries=file_summaries, package_id=package_id)
    package_summary = summarize_package(store, package_path=root_path, module_summaries=[module_summary], package_id=package_id)
    return chunk_summaries, file_summaries, module_summary, package_summary


def summarize_chunks(store: Store, file_id: int) -> List[SummaryRecord]:
    """
    Summarize each chunk within a file.
    """
    file_rec = store.get_file_by_id(file_id)
    if not file_rec:
        raise ValueError(f"file_id {file_id} not found")
    chunk_summaries: List[SummaryRecord] = []
    for chunk in store.get_chunks_for_file(file_id):
        summ_module = SummarizeFileModule()
        result = summ_module(file_path=file_rec.path, content=chunk.text)
        text = " ".join(result["text"].split())
        confidence = float(result.get("confidence", 0.5))
        citation = generate_citation_from_chunk(chunk, file_rec.path)
        summary = SummaryRecord(
            level="chunk",
            target_id=chunk.id or -1,
            text=f"{text} [{citation}]",
            confidence=confidence,
            created_at=datetime.now(timezone.utc),
        )
        summary_id = store.add_summary(summary)
        summary.id = summary_id
        validate_summary(store, summary)
        chunk_summaries.append(summary)
    return chunk_summaries


def summarize_module(store: Store, module_path: str, file_summaries: List[SummaryRecord], package_id: int | None = None) -> SummaryRecord:
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
        # include first few citations to ground module summary
        citation_suffix = f" [{' '.join(child_citations[:3])}]"
    module_target = store.add_module(module_path, Path(module_path).name, package_id)
    for fs in file_summaries:
        if fs.level == "file":
            store.link_file_to_module(module_target, fs.target_id)
    summary = SummaryRecord(
        level="module",
        target_id=module_target,
        text=" ".join(result["text"].split()) + citation_suffix,
        confidence=float(result.get("confidence", 0.5)),
        created_at=datetime.now(timezone.utc),
    )
    summary_id = store.add_summary(summary)
    summary.id = summary_id
    validate_summary(store, summary)
    return summary


def summarize_package(store: Store, package_path: str, module_summaries: List[SummaryRecord], package_id: int | None = None) -> SummaryRecord:
    """
    Aggregate module summaries into a package-level summary using DSPy reduce module.
    """
    reduce_module = SummarizeModuleModule()
    result = reduce_module(module_path=package_path, child_summaries=[s.text for s in module_summaries])
    child_citations = []
    for s in module_summaries:
        for token in s.text.split():
            if token.startswith("[") and token.endswith("]"):
                try:
                    validate_citation(token.strip("[]"))
                    child_citations.append(token.strip("[]"))
                except Exception:
                    continue
    citation_suffix = ""
    if child_citations:
        citation_suffix = f" [{' '.join(child_citations[:3])}]"
    pkg_id = package_id or store.add_package(package_path, Path(package_path).name)
    package_target = pkg_id
    summary = SummaryRecord(
        level="package",
        target_id=package_target,
        text=" ".join(result["text"].split()) + citation_suffix,
        confidence=float(result.get("confidence", 0.5)),
        created_at=datetime.now(timezone.utc),
    )
    summary_id = store.add_summary(summary)
    summary.id = summary_id
    validate_summary(store, summary)
    return summary
