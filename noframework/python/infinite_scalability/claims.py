import re
from typing import Callable, List, Optional, Set

from .citations import validate_citation

from .models import ClaimRecord, ClaimStatus, Severity
from .retrieval import retrieve_context
from .llm import summarize_text
from .store import Store


def _parse_citations(text: str) -> List[str]:
    tokens = re.findall(r"\[([^\]]+)\]", text)
    valid: List[str] = []
    for tok in tokens:
        try:
            validate_citation(tok)
            valid.append(tok)
        except Exception:
            continue
    return valid


def extract_claims(report_text: str, report_version: int) -> List[ClaimRecord]:
    """
    Extract claims generically: bullets or paragraphs with optional citations.
    Headers/blank lines are ignored. Only valid citations are retained.
    """
    claims: List[ClaimRecord] = []
    for line in report_text.splitlines():
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        if text.startswith("- ") or len(text.split()) >= 5:
            citations = _parse_citations(text)
            claims.append(
                ClaimRecord(
                    report_version=report_version,
                    text=text,
                    citation_refs=citations,
                    status=ClaimStatus.MISSING,
                    severity=Severity.MEDIUM,
                    rationale="Not checked",
                )
            )
    return claims


def _grade_claim(
    claim_text: str, evidence: str, grader: Callable[[str, str], dict | str] | None = None
) -> dict:
    """
    Grade whether evidence supports the claim using an LLM-backed grader.
    Returns structured dict: {status: supported|contradicted|uncertain, rationale: str}.
    """
    if grader:
        res = grader(claim_text, evidence)
        if isinstance(res, dict):
            return res
        low = str(res).lower()
        status = "uncertain"
        if "supported" in low:
            status = "supported"
        elif "contradicted" in low:
            status = "contradicted"
        return {"status": status, "rationale": str(res)}
    result = summarize_text(
        f"Claim: {claim_text}\n\nEvidence:\n{evidence}",
        instructions="State if the evidence supports the claim. Respond with JSON: {\"status\": \"supported|contradicted|uncertain\", \"rationale\": \"...\"}.",
    )
    try:
        data = result.model_dump()  # type: ignore[attr-defined]
    except Exception:
        # fallback: parse keywords
        low = result.text.lower()
        status = "uncertain"
        if "supported" in low:
            status = "supported"
        elif "contradicted" in low:
            status = "contradicted"
        data = {"status": status, "rationale": result.text}
    return data


def _severity_from_status(status: ClaimStatus) -> Severity:
    if status == ClaimStatus.SUPPORTED:
        return Severity.LOW
    if status == ClaimStatus.UNCERTAIN:
        return Severity.MEDIUM
    return Severity.HIGH


def check_claims(
    store: Store,
    claims: List[ClaimRecord],
    grader: Callable[[str, str], str] | None = None,
    allowed_citations: Optional[Set[str]] = None,
) -> List[ClaimRecord]:
    """
    Claim verification: validate citations, grade support, and attempt repair via retrieval.
    """
    checked: List[ClaimRecord] = []
    for claim in claims:
        supported = False
        contradicted = False
        rationale = "No supporting chunk found"
        graded_text = None
        repaired_citations = []

        # Validate citations against store
        for cit in claim.citation_refs:
            if allowed_citations and cit not in allowed_citations:
                continue
            try:
                path, start, end = validate_citation(cit)
            except Exception:
                continue
            file_rec = store.get_file_by_path(path)
            if not file_rec:
                continue
            chunk = store.find_chunk_covering_range(file_rec.id, start, end)
            if not chunk:
                continue
            repaired_citations.append(cit)
            graded = _grade_claim(claim.text, chunk.text, grader)
            graded_text = graded.get("rationale", "")
            status_val = graded.get("status", "").lower()
            if "contradicted" in status_val:
                contradicted = True
                rationale = f"Contradicted by {cit}"
                break
            if "supported" in status_val:
                supported = True
                rationale = f"Supported by {cit}"
                break

        claim.citation_refs = repaired_citations

        # Try to find supporting evidence if none validated
        if not supported and not contradicted:
            ctx = retrieve_context(store, claim.text, limit=5)
            for c in ctx.chunks:
                graded = _grade_claim(claim.text, c.text, grader)
                graded_text = graded.get("rationale", "")
                status_val = graded.get("status", "").lower()
                fpath = store.get_file_by_id(c.file_id).path  # type: ignore
                citation = f"{fpath}:{c.start_line}-{c.end_line}"
                if allowed_citations and citation not in allowed_citations:
                    continue
                if "contradicted" in status_val:
                    contradicted = True
                    rationale = f"Contradicted by {citation}"
                    repaired_citations.append(citation)
                    break
                if "supported" in status_val:
                    supported = True
                    rationale = f"Supported by {citation}"
                    repaired_citations.append(citation)
                    break

        if contradicted:
            claim.status = ClaimStatus.CONTRADICTED
        elif supported:
            claim.status = ClaimStatus.SUPPORTED
        else:
            claim.status = ClaimStatus.MISSING

        claim.severity = _severity_from_status(claim.status)
        claim.rationale = graded_text or rationale
        checked.append(claim)
    return checked
