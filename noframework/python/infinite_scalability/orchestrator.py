from pathlib import Path
from typing import Tuple

from .claims import check_claims, extract_claims
from .coverage import assess_coverage, plan_issues, gate_should_continue
from .ingest import ingest_repo
from .models import ReportVersionRecord, Severity, CoverageGate
from .retrieval import retrieve_context
from .store import Store
from .summarize import summarize_all_files, summarize_module
from .citations import generate_citation_from_chunk
from .repair import repair_report
from .enforcement import enforce_draft_citations, validate_report_citations
from .llm import draft_report


def run_pipeline(root: Path, prompt: str, store: Store, gate: CoverageGate | None = None, max_iters: int = 3) -> Tuple[str, ReportVersionRecord]:
    """
    End-to-end pipeline for arbitrary prompts. Ingests, summarizes, retrieves context,
    and builds a prompt-driven report with citations.
    """
    ingest_repo(root, store)
    summaries = summarize_all_files(store)
    module_summary = summarize_module(store, module_path=str(root), file_summaries=summaries)

    ctx = retrieve_context(store, prompt, limit=20)
    evidence_blocks: list[str] = []
    for chunk in ctx.chunks:
        file_rec = store.get_file_by_id(chunk.file_id)
        if not file_rec:
            continue
        citation = generate_citation_from_chunk(chunk, file_rec.path)
        evidence_blocks.append(f"[{citation}] {chunk.text.strip()}")
    for summary in summaries + [module_summary]:
        evidence_blocks.append(summary.text)

    if not evidence_blocks:
        raise RuntimeError("No evidence collected for the prompt; cannot draft a report.")

    report_md = draft_report(prompt, evidence_blocks)
    report_md = enforce_draft_citations(report_md, store, prompt)
    validate_report_citations(report_md, store)

    # create report version stub
    rv = ReportVersionRecord(
        content=report_md,
        coverage_score=0.0,
        citation_score=0.0,
        issues_high=0,
        issues_med=0,
        issues_low=0,
    )
    rv_id = store.add_report_version(rv)
    rv.id = rv_id

    last_metrics = {}
    for attempt in range(max_iters):
        store.conn.execute("DELETE FROM claims WHERE report_version=?", (rv_id,))
        claims = extract_claims(report_md, report_version=rv_id)
        claims = check_claims(store, claims)
        # Attempt repair of missing citations if still missing
        if any(not c.citation_refs for c in claims):
            report_md, claims = repair_report(report_md, store, rv_id)
            claims = [c for c in claims if c.status]  # ensure valid
        store.add_claims(claims)

        coverage = assess_coverage(store=store, claims=claims)
        rv.coverage_score = coverage.score
        support_rate = sum(1 for c in claims if c.status == c.status.SUPPORTED) / (len(claims) or 1)
        citation_rate = sum(1 for c in claims if c.citation_refs) / (len(claims) or 1)
        rv.citation_score = citation_rate
        rv.issues_high = sum(1 for c in claims if c.severity == Severity.HIGH)
        rv.issues_med = sum(1 for c in claims if c.severity == Severity.MEDIUM)
        rv.issues_low = sum(1 for c in claims if c.severity == Severity.LOW)
        store.conn.execute(
            "UPDATE report_versions SET coverage_score=?, citation_score=?, issues_high=?, issues_med=?, issues_low=? WHERE id=?",
            (rv.coverage_score, rv.citation_score, rv.issues_high, rv.issues_med, rv.issues_low, rv_id),
        )
        store.conn.commit()

        if gate is None:
            break
        last_metrics = {
            "coverage": coverage.score,
            "support_rate": support_rate,
            "citation_rate": citation_rate,
            "missing_citations": sum(1 for c in claims if not c.citation_refs),
            "issues_high": rv.issues_high,
            "issues_med": rv.issues_med,
        }

        # Plan issues for potential revision (future step)
        issues = plan_issues(coverage, claims)

        if not gate_should_continue(gate, coverage, claims):
            break
        # simple revision step: re-run citation enforcement using planned issues context
        report_md = enforce_draft_citations(report_md, store, prompt)
        validate_report_citations(report_md, store)
        if attempt == max_iters - 1:
            raise RuntimeError(f"Gating failed after {max_iters} attempts: {last_metrics}, issues={len(issues)}")

    return report_md, rv
