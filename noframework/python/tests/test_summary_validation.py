from pathlib import Path
import pytest

from infinite_scalability.summarize import summarize_file, summarize_module
from infinite_scalability.validation import validate_summary
from infinite_scalability.ingest import ingest_repo
from infinite_scalability.store import Store


def test_summarize_and_validate_file(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "code.py").write_text("def foo():\n    return 1\n")
    store = Store(persist=False)
    ingest_repo(repo, store)
    file_rec = store.get_all_files()[0]
    summary = summarize_file(store, file_rec.id)  # type: ignore
    validate_summary(store, summary)
    store.close()


def test_module_summary_inherits_citation(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "code.py").write_text("def foo():\n    return 1\n")
    store = Store(persist=False)
    ingest_repo(repo, store)
    file_rec = store.get_all_files()[0]
    summary = summarize_file(store, file_rec.id)  # type: ignore
    module_summary = summarize_module(store, "module", [summary])
    validate_summary(store, module_summary)
    store.close()


def test_validate_summary_missing_citation_raises(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "code.py").write_text("def foo():\n    return 1\n")
    store = Store(persist=False)
    ingest_repo(repo, store)
    bad = summary = summarize_file(store, store.get_all_files()[0].id)  # type: ignore
    bad.text = "No citations here"
    with pytest.raises(ValueError):
        validate_summary(store, bad)
    store.close()
