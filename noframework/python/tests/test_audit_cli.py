import subprocess
import sys
from pathlib import Path

from infinite_scalability.ingest import ingest_repo
from infinite_scalability.store import Store
from infinite_scalability.orchestrator import run_pipeline


def test_audit_cli_lists(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "code.py").write_text("def foo():\n    return 1\n")
    prompt = "Describe"
    store_path = tmp_path / "store.db"
    store = Store(db_path=store_path, persist=True)
    run_pipeline(repo, prompt, store)
    store.close()

    cmds = [
        ["-m", "infinite_scalability.audit_cli", str(store_path), "list-files"],
        ["-m", "infinite_scalability.audit_cli", str(store_path), "list-reports"],
        ["-m", "infinite_scalability.audit_cli", str(store_path), "list-claims", "--report-id", "1"],
        ["-m", "infinite_scalability.audit_cli", str(store_path), "list-symbols"],
        ["-m", "infinite_scalability.audit_cli", str(store_path), "search-chunks", "--query", "foo"],
        ["-m", "infinite_scalability.audit_cli", str(store_path), "list-summaries"],
        ["-m", "infinite_scalability.audit_cli", str(store_path), "symbol-neighbors", "--symbol-id", "1"],
        ["-m", "infinite_scalability.audit_cli", str(store_path), "export-report", "--id", "1", "--out", str(tmp_path / "out.md")],
    ]
    for cmd in cmds:
        res = subprocess.run([sys.executable] + cmd, capture_output=True, text=True)
        assert res.returncode == 0, res.stderr
