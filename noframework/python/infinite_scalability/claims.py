from typing import List

from .models import ClaimRecord, ClaimStatus, Severity
from .retrieval import retrieve_context
from .llm import summarize_text
from .store import Store


def extract_claims(report_text: str, report_version: int) -> List[ClaimRecord]:
    """
    Extract claims: bullet lines and paragraphs with optional citation markers [path:start-end].
    """
    claims: List[ClaimRecord] = []
    for line in report_text.splitlines():
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        if text.startswith("- ") or len(text.split()) > 5:
            citations = []
            if "[" in text and "]" in text:
                # crude extraction of citation blocks like [path:start-end]
                parts = [seg for seg in text.split() if seg.startswith("[") and seg.endswith("]")]
                citations = [p.strip("[]") for p in parts]
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


def check_claims(store: Store, claims: List[ClaimRecord]) -> List[ClaimRecord]:
    """
    Claim verification: validate citations and grade support; repair citations if needed.
    """
    checked: List[ClaimRecord] = []
    for claim in claims:
        supported = False
        rationale = "No supporting chunk found"
        graded_text = None
        repaired_citations = []
        # validate/repair citations
        for cit in claim.citation_refs:
            if ":" in cit and "-" in cit:
                path, span = cit.split(":", 1)
                start_str, end_str = span.split("-")
                try:
                    start, end = int(start_str), int(end_str)
                    file_rec = store.get_file_by_path(path)
                    if file_rec:
                        chunk = store.find_chunk_covering_range(file_rec.id, start, end)
                        if chunk:
                            repaired_citations.append(cit)
                            # check semantic support via LLM
                            grade = summarize_text(
                                f"Claim: {claim.text}\n\nEvidence:\n{chunk.text}",
                                instructions="State if the evidence supports the claim. Respond with 'supported' or 'contradicted' and a short rationale.",
                            )
                            graded_text = grade.text
                            if "supported" in grade.text.lower():
                                supported = True
                                rationale = f"LLM graded supported for {path}:{chunk.start_line}-{chunk.end_line}"
                                break
                except ValueError:
                    continue
        claim.citation_refs = repaired_citations

        if not supported:
            # try to find better citations via retrieval
            ctx = retrieve_context(store, claim.text, limit=5)
            for c in ctx.chunks:
                grade = summarize_text(
                    f"Claim: {claim.text}\n\nEvidence:\n{c.text}",
                    instructions="State if the evidence supports the claim. Respond with 'supported' or 'contradicted' and a short rationale.",
                )
                if "supported" in grade.text.lower():
                    supported = True
                    graded_text = grade.text
                    fpath = store.get_file_by_id(c.file_id).path  # type: ignore
                    citation = f"{fpath}:{c.start_line}-{c.end_line}"
                    claim.citation_refs.append(citation)
                    rationale = f"LLM graded supported via retrieval chunk {citation}"
                    break

        if supported:
            claim.status = ClaimStatus.SUPPORTED
            claim.severity = Severity.LOW
            claim.rationale = graded_text or rationale
        else:
            claim.status = ClaimStatus.MISSING
            claim.severity = Severity.HIGH
            claim.rationale = "No supporting chunk found after repair"
        checked.append(claim)
    return checked
