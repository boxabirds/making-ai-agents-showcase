from pathlib import Path

from datetime import datetime, timezone

from infinite_scalability.claims import extract_claims, check_claims
from infinite_scalability.models import ClaimStatus
from infinite_scalability.store import Store


def test_extract_claims_validates_citations():
    report = """
# Header
- Bullet without citation
- Supported claim [file.py:1-2]
Paragraph with bad citation [bad]
"""
    claims = extract_claims(report, report_version=1)
    # Expect three claims (two bullets + paragraph), but only one valid citation retained
    assert len(claims) == 3
    cited = [c for c in claims if c.citation_refs]
    assert len(cited) == 1
    assert cited[0].citation_refs == ["file.py:1-2"]


def test_check_claims_supports_with_retrieval(tmp_path: Path):
    """
    Use a deterministic grader to avoid live LLM calls and ensure supported status is set.
    """
    store = Store(persist=False)
    from infinite_scalability.models import FileRecord, ChunkRecord

    file_rec = FileRecord(
        path="code.py",
        hash="h",
        lang="py",
        size=1,
        mtime=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    fid = store.add_file(file_rec)
    chunk = ChunkRecord(
        file_id=fid,
        start_line=1,
        end_line=2,
        kind="function",
        text="def foo():\n    return 1\n",
        hash="ch",
    )
    store.add_chunks([chunk])

    claims = extract_claims("- Claim about foo [code.py:1-2]", report_version=1)

    # Deterministic grader that always says supported
    def grader(claim_text: str, evidence: str) -> str:
        return "supported: evidence matches"

    checked = check_claims(store, claims, grader=grader)
    assert checked[0].status == ClaimStatus.SUPPORTED
    assert checked[0].severity.value == "low"
    store.close()
