import runpy
from pathlib import Path


def test_format_jobs_has_superset_columns():
    repo = Path(__file__).resolve().parents[1]
    script = repo / "bin" / "mqtop"
    mod = runpy.run_path(str(script))

    jobs = [
        {
            "id": "1",
            "name": "run",
            "walltime_used": 10,
            "walltime_total": 20,
            "ncpus": 2,
            "mem_request_gb": 4,
            "state": "R",
            "queue": "cpu",
            "cpupercent": 50,
            "ncpus_used": 2,
            "mem_usage": 2 * 1024 * 1024,
        },
        {
            "id": "2",
            "name": "done",
            "walltime_used": 10,
            "walltime_total": 20,
            "ncpus": 1,
            "mem_request_gb": 2,
            "state": "C",
            "queue": "cpu",
            "cput_used": 10,
            "vmem_used_kb": 1024 * 1024,
        },
    ]

    lines, rows = mod["format_jobs"](jobs)
    header = lines[0]
    for col in ["waited", "cpu%", "ram%", "state"]:
        assert col in header
    assert len(rows) == 2

