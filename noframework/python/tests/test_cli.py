import subprocess
import sys
from pathlib import Path


def run_cli(tmp_path: Path, persist: bool):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("hello\n")
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Test prompt")
    store_path = tmp_path / "store.db"
    cmd = [
        sys.executable,
        "-m",
        "infinite_scalability.cli",
        "--prompt",
        str(prompt),
        "--store-path",
        str(store_path),
    ]
    if persist:
        cmd.append("--persist-store")
    cmd.append(str(repo))
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    return store_path


def test_cli_ephemeral(tmp_path: Path):
    store_path = run_cli(tmp_path, persist=False)
    assert not store_path.exists()


def test_cli_persist(tmp_path: Path):
    store_path = run_cli(tmp_path, persist=True)
    assert store_path.exists()
