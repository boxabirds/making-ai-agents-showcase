import os
import subprocess
import sys
from pathlib import Path


def test_eval_runner_axios(tmp_path: Path):
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("Produce a concise architecture overview.")
    metrics_out = tmp_path / "metrics.json"
    env = os.environ.copy()
    env["INGEST_FILE_LIMIT"] = "4"
    cmd = [
        sys.executable,
        "-m",
        "infinite_scalability.eval_runner",
        "--prompt",
        str(prompt),
        "--repo",
        "https://github.com/axios/axios",
        "--metrics-out",
        str(metrics_out),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=360)
    assert res.returncode == 0, res.stderr
    assert metrics_out.exists()
