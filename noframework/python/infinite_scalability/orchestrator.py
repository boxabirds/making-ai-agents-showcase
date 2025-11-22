from pathlib import Path
from typing import Tuple

from .claims import check_claims, extract_claims
from .coverage import assess_coverage
from .ingest import ingest_repo
from .models import ReportVersionRecord, Severity, CoverageGate
from .retrieval import retrieve_context
from .store import Store
from .summarize import summarize_all_files, summarize_module
from .citations import generate_citation_from_chunk
from .repair import repair_report
from .enforcement import enforce_draft_citations, validate_report_citations


def run_pipeline(root: Path, prompt: str, store: Store, gate: CoverageGate | None = None, max_iters: int = 3) -> Tuple[str, ReportVersionRecord]:
    """
    End-to-end pipeline for arbitrary prompts. Ingests, summarizes, retrieves context,
    and builds a prompt-driven report with citations.
    """
    ingest_repo(root, store)
    summaries = summarize_all_files(store)
    module_summary = summarize_module(store, module_path=str(root), file_summaries=summaries)

    ctx = retrieve_context(store, prompt, limit=20)
    report_lines = [f"# Tech Writer Report", f"Prompt: {prompt}", ""]
    report_lines.append("## Summaries")
    for s in summaries + [module_summary]:
        report_lines.append(s.text)
        report_lines.append("")
    report_lines.append("## Retrieved Context")
    citations = []
    for c in ctx.chunks[:5]:
        snippet = c.text.strip().splitlines()[0] if c.text.strip() else ""
        citation = generate_citation_from_chunk(c, store.get_file_by_id(c.file_id).path)  # type: ignore
        citations.append(citation)
        report_lines.append(f"- {c.kind} [{citation}]: {snippet}")
    if citations:
        report_lines.append("")
        report_lines.append("## Citations")
        for cit in citations:
            report_lines.append(f"- [{cit}]")
    report_md = "\n".join(report_lines)
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

        # expected surface = symbols per file (rough proxy)
        expected_items = 0
        for f in store.get_all_files():
            expected_items += len(store.get_symbols_for_file(f.id))
        expected_items = max(expected_items, len(summaries))
        coverage = assess_coverage(expected_items=expected_items, claims=claims)
        rv.coverage_score = coverage.score
        rv.citation_score = 0.0
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
        total_claims = len(claims) or 1
        support_rate = sum(1 for c in claims if c.status == c.status.SUPPORTED) / total_claims
        citation_rate = sum(1 for c in claims if c.citation_refs) / total_claims
        missing_citations = sum(1 for c in claims if not c.citation_refs)
        last_metrics = {
            "coverage": coverage.score,
            "support_rate": support_rate,
            "citation_rate": citation_rate,
            "missing_citations": missing_citations,
            "issues_high": rv.issues_high,
            "issues_med": rv.issues_med,
        }
        if (
            rv.issues_high <= gate.max_high_issues
            and rv.issues_med <= gate.max_medium_issues
            and coverage.score >= gate.min_coverage
            and support_rate >= gate.min_support_rate
            and citation_rate >= gate.min_citation_rate
            and missing_citations == 0
        ):
            break
        if attempt == max_iters - 1:
            raise RuntimeError(f"Gating failed after {max_iters} attempts: {last_metrics}")

    return report_md, rv
