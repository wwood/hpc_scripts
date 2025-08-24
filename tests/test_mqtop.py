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


def test_short_runtime_not_coloured_red():
    repo = Path(__file__).resolve().parents[1]
    script = repo / "bin" / "mqtop"
    mod = runpy.run_path(str(script))

    jobs = [
        {
            "id": "1",
            "name": "short",
            "walltime_used": 100,
            "walltime_total": 200,
            "ncpus": 1,
            "mem_request_gb": 1,
            "state": "R",
            "queue": "cpu",
            "cpupercent": 5,
            "ncpus_used": 1,
            "mem_usage": 512 * 1024,
        }
    ]

    lines, _ = mod["format_jobs"](jobs)
    assert "\033[91m" not in lines[1]

