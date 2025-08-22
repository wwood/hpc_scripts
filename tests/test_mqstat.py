import subprocess
import sys
from pathlib import Path


def test_mqstat_list():
    repo = Path(__file__).resolve().parents[1]
    script = repo / "bin" / "mqstat"
    qstat_file = repo / "tests" / "data" / "qstat_f.txt"
    result = subprocess.run(
        [sys.executable, str(script), "--list", "--qstat-file", str(qstat_file)],
        text=True,
        capture_output=True,
        check=True,
    )
    lines = result.stdout.strip().splitlines()
    assert lines[0].split("\t") == [
        "job_id",
        "name",
        "time used",
        "time remaining",
        "queue",
        "RAM",
        "CPU",
        "state",
    ]
    assert lines[1].split("\t") == [
        "123.server",
        "testjob",
        "00:10:00",
        "00:50:00",
        "batch",
        "4G",
        "4",
        "R",
    ]
    assert lines[2].split("\t") == [
        "456.server",
        "bigmem",
        "00:30:00",
        "01:30:00",
        "batch",
        "256G🧠",
        "8",
        "R",
    ]
    assert lines[3].split("\t") == [
        "789.server",
        "bigcpu",
        "00:00:00",
        "03:00:00",
        "batch",
        "64G",
        "32💪",
        "Q",
    ]

