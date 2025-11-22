import json
from typing import Dict, List

from .models import ClaimRecord, Severity
from .store import Store


def evaluate_metrics(store: Store, report_version_id: int, expected_items: int) -> Dict[str, float]:
    """
    Compute basic support, coverage, citation rates for a report version.
    """
    cur = store.conn.execute(
        "SELECT text, citation_refs, status FROM claims WHERE report_version=?", (report_version_id,)
    )
    rows = cur.fetchall()
    claims: List[ClaimRecord] = []
    for r in rows:
        citations = []
        if r[1]:
            try:
                citations = json.loads(r[1])
            except Exception:
                citations = []
        claims.append(
            ClaimRecord(
                report_version=report_version_id,
                text=r[0],
                citation_refs=citations,
                status=r[2],
                severity=Severity.LOW,  # severity not used for metrics; set default
                rationale="",
            )
        )
    total = len(claims) or 1
    supported = sum(1 for c in claims if c.status == c.status.SUPPORTED)
    with_citations = sum(1 for c in claims if c.citation_refs)
    support_rate = supported / total
    citation_rate = with_citations / total
    coverage = min(1.0, supported / (expected_items or 1))
    return {
        "support_rate": support_rate,
        "citation_rate": citation_rate,
        "coverage": coverage,
    }
