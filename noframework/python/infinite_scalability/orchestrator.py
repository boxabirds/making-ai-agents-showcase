from pathlib import Path
from typing import Tuple

from .claims import check_claims, extract_claims
from .coverage import assess_coverage, plan_issues, gate_should_continue
from .ingest import ingest_repo
from .models import ReportVersionRecord, Severity, CoverageGate
from .retrieval import retrieve_context
from .store import Store
from .summarize import summarize_all_files, summarize_module, summarize_project
from .citations import generate_citation_from_chunk, validate_citation
from .repair import repair_report, revise_report
from .enforcement import enforce_draft_citations, validate_report_citations
from .llm import draft_report


def run_pipeline(root: Path, prompt: str, store: Store, gate: CoverageGate | None = None, max_iters: int = 3) -> Tuple[str, ReportVersionRecord]:
    """
    End-to-end pipeline for arbitrary prompts. Ingests, summarizes, retrieves context,
    and builds a prompt-driven report with citations.
    """
    ingest_repo(root, store)
    chunk_summaries, file_summaries, module_summary, package_summary = summarize_project(store, root_path=str(root))

    def build_evidence(topic: str):
        ctx = retrieve_context(store, topic, limit=20)
        blocks: list[str] = []
        for chunk in ctx.chunks:
            file_rec = store.get_file_by_id(chunk.file_id)
            if not file_rec:
                continue
            citation = generate_citation_from_chunk(chunk, file_rec.path)
            blocks.append(f"[{citation}] {chunk.text.strip()}")
        return ctx, blocks

    ctx, evidence_blocks = build_evidence(prompt)

    if not evidence_blocks:
        raise RuntimeError("No evidence collected for the prompt; cannot draft a report.")

    report_md = draft_report(prompt, evidence_blocks)
    # build allowed citations from evidence blocks
    def allowed_from_blocks(blocks: list[str]) -> set[str]:
        allowed = set()
        for block in blocks:
            for token in block.split():
                if token.startswith("[") and token.endswith("]"):
                    cit = token.strip("[]")
                    try:
                        validate_citation(cit)
                        allowed.add(cit)
                    except Exception:
                        continue
        return allowed

    allowed_citations = allowed_from_blocks(evidence_blocks)
    report_md = enforce_draft_citations(report_md, store, prompt, allowed_citations=allowed_citations)
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
    store.log_retrieval_event(
        report_version=rv_id,
        iteration=0,
        prompt=prompt,
        chunks=ctx.chunks,
        summaries=[],
        symbols=ctx.symbols,
        edges=ctx.edges,
    )

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
        missing_citations = sum(1 for c in claims if not c.citation_refs)
        rv.citation_score = citation_rate
        rv.issues_high = sum(1 for c in claims if c.severity == Severity.HIGH)
        rv.issues_med = sum(1 for c in claims if c.severity == Severity.MEDIUM)
        rv.issues_low = sum(1 for c in claims if c.severity == Severity.LOW)
        store.conn.execute(
            "UPDATE report_versions SET coverage_score=?, citation_score=?, issues_high=?, issues_med=?, issues_low=? WHERE id=?",
            (rv.coverage_score, rv.citation_score, rv.issues_high, rv.issues_med, rv.issues_low, rv_id),
        )
        store.conn.commit()
        issues = plan_issues(coverage, claims)
        store.log_iteration_status(
            report_version=rv_id,
            iteration=attempt,
            coverage=coverage.score,
            support_rate=support_rate,
            citation_rate=citation_rate,
            issues_high=rv.issues_high,
            issues_med=rv.issues_med,
            issues_low=rv.issues_low,
            missing_citations=missing_citations,
        )
        store.log_iteration_issues(rv_id, attempt, issues)

        if gate is None:
            break
        last_metrics = {
            "coverage": coverage.score,
            "support_rate": support_rate,
            "citation_rate": citation_rate,
            "missing_citations": missing_citations,
            "issues_high": rv.issues_high,
            "issues_med": rv.issues_med,
        }

        if not gate_should_continue(gate, coverage, claims):
            break
        # Issue-driven revision: re-draft with issues guidance and enforce allowed citations
        issues_text = "\n".join([f"- {iss.description} ({iss.severity.value})" for iss in issues])
        guidance_prompt = "\n".join(
            [
                prompt,
                "",
                "Please revise the draft to address these issues:",
                issues_text or "- No issues provided; ensure citations are present and correct.",
            ]
        )
        ctx, evidence_blocks = build_evidence(prompt)
        allowed_citations = allowed_from_blocks(evidence_blocks)
        report_md = draft_report(guidance_prompt, evidence_blocks)
        report_md = enforce_draft_citations(report_md, store, prompt, allowed_citations=allowed_citations)
        validate_report_citations(report_md, store)
        rv.content = report_md
        store.conn.execute("UPDATE report_versions SET content=? WHERE id=?", (rv.content, rv_id))
        store.conn.commit()
        store.log_retrieval_event(
            report_version=rv_id,
            iteration=attempt + 1,
            prompt=prompt,
            chunks=ctx.chunks,
            summaries=[],
            symbols=ctx.symbols,
            edges=ctx.edges,
        )
        if attempt == max_iters - 1:
            raise RuntimeError(f"Gating failed after {max_iters} attempts: {last_metrics}, issues={len(issues)}")

    return report_md, rv
