from datetime import datetime, timezone

from infinite_scalability.coverage import assess_coverage, plan_issues, gate_should_continue
from infinite_scalability.models import ClaimRecord, ClaimStatus, Severity, CoverageGate, FileRecord, ChunkRecord
from infinite_scalability.store import Store


def _store_with_symbol(tmp_path):
    store = Store(persist=False)
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
    store.conn.execute(
        "INSERT INTO symbols(file_id, name, kind, signature, start_line, end_line, doc, parent_symbol_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (fid, "foo", "function", None, 1, 2, None, None),
    )
    store.conn.commit()
    return store


def test_assess_coverage_counts_targets(tmp_path):
    store = _store_with_symbol(tmp_path)
    claims = [
        ClaimRecord(
            report_version=1,
            text="- Implements foo (code.py::foo) [code.py:1-2]",
            citation_refs=["code.py:1-2"],
            status=ClaimStatus.SUPPORTED,
            severity=Severity.LOW,
            rationale="supported",
        )
    ]
    result = assess_coverage(store, claims)
    assert result.expected == 1
    assert result.covered == 1
    assert result.score == 1.0
    store.close()


def test_plan_issues_includes_missing_and_claim_failures(tmp_path):
    store = _store_with_symbol(tmp_path)
    claims = [
        ClaimRecord(
            report_version=1,
            text="- Missing support [code.py:1-2]",
            citation_refs=["code.py:1-2"],
            status=ClaimStatus.MISSING,
            severity=Severity.HIGH,
            rationale="missing",
        )
    ]
    coverage = assess_coverage(store, claims)
    issues = plan_issues(coverage, claims)
    assert any("Missing coverage" in i.description for i in issues)
    assert any("Claim unresolved" in i.description for i in issues)
    # high issues first
    assert issues[0].severity == Severity.HIGH
    store.close()


def test_gate_should_continue(tmp_path):
    store = _store_with_symbol(tmp_path)
    claims = [
        ClaimRecord(
            report_version=1,
            text="- Implements foo (code.py::foo) [code.py:1-2]",
            citation_refs=["code.py:1-2"],
            status=ClaimStatus.SUPPORTED,
            severity=Severity.LOW,
            rationale="supported",
        )
    ]
    coverage = assess_coverage(store, claims)
    gate = CoverageGate(min_support_rate=0.5, min_coverage=0.5, min_citation_rate=0.5, max_high_issues=0, max_medium_issues=1)
    assert gate_should_continue(gate, coverage, claims) is False
    store.close()
