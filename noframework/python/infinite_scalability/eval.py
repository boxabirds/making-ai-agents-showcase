import json
from typing import Dict, List

from .models import ClaimRecord, Severity
from .store import Store
from .citations import validate_citation
from .claims import extract_claims, check_claims
from .enforcement import validate_report_citations


def evaluate_metrics(store: Store, report_version_id: int, expected_items: int) -> Dict[str, float]:
    """
    Recompute support/coverage/citation rates by re-extracting claims from the stored report and rechecking citations.
    """
    cur = store.conn.execute("SELECT content FROM report_versions WHERE id=?", (report_version_id,))
    row = cur.fetchone()
    if not row:
        raise ValueError("report_version not found")
    report_text = row[0]
    validate_report_citations(report_text, store)
    claims = extract_claims(report_text, report_version=report_version_id)
    # deterministic grader: supported if a valid citation maps to a chunk
    def grader(claim_text: str, evidence: str) -> dict:
        return {"status": "supported", "rationale": "matched citation"}
    claims = check_claims(store, claims, grader=grader)
    total = len(claims) or 1
    with_citations = sum(1 for c in claims if c.citation_refs)
    supported = sum(1 for c in claims if c.status == c.status.SUPPORTED)
    support_rate = supported / total
    citation_rate = with_citations / total
    coverage = min(1.0, supported / (expected_items or 1))
    # Citation veracity: validate citations map to stored chunks
    total_citations = 0
    valid_citations = 0
    for c in claims:
        for cit in c.citation_refs:
            total_citations += 1
            try:
                path, start, end = validate_citation(cit)
            except Exception:
                continue
            file_rec = store.get_file_by_path(path)
            if not file_rec:
                continue
            chunk = store.find_chunk_covering_range(file_rec.id, start, end)
            if chunk:
                valid_citations += 1
    veracity_rate = valid_citations / total_citations if total_citations else 1.0

    return {
        "support_rate": support_rate,
        "citation_rate": citation_rate,
        "coverage": coverage,
        "citation_veracity_rate": veracity_rate,
        "total_claims": total,
        "total_citations": total_citations,
    }
