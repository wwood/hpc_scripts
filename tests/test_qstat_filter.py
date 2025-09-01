import json
import subprocess
from pathlib import Path


def test_qstat_filter_outputs_only_requested_user():
    repo = Path(__file__).resolve().parents[1]
    crate = repo / "qstat_filter"
    bin_path = crate / "target" / "release" / "qstat_filter"

    if not bin_path.exists():
        subprocess.run(["cargo", "build", "--release"], cwd=crate, check=True)

    proc = subprocess.run(
        [
            str(bin_path),
            str(repo / "tests" / "data" / "qstat.json"),
            "root",
        ],
        text=True,
        capture_output=True,
        check=True,
    )

    lines = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
    assert lines, "qstat_filter produced no output"
    assert all(job.get("euser") == "root" for job in lines)
    assert all("id" in job for job in lines)
