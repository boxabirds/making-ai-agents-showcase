from .claims import extract_claims, check_claims
from .models import ClaimRecord
from .store import Store
from .enforcement import enforce_draft_citations, validate_report_citations


def repair_report(report_md: str, store: Store, report_version_id: int) -> tuple[str, list[ClaimRecord]]:
    """
    Repair report by re-checking claims and fixing missing citations if possible.
    """
    # Remove existing claims and regenerate
    claims = extract_claims(report_md, report_version=report_version_id)
    claims = check_claims(store, claims)
    # ensure report_version set
    for c in claims:
        c.report_version = report_version_id
    return report_md, claims


def revise_report(report_md: str, store: Store, topic: str, allowed_citations: set[str] | None = None) -> str:
    """
    Revise a report by enforcing/repairing citations while preserving content.
    """
    revised = enforce_draft_citations(report_md, store, topic, allowed_citations=allowed_citations)
    validate_report_citations(revised, store)
    return revised
