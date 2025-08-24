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
    for col in ["waited", "age", "cpu%", "ram%", "state"]:
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
def test_waited_zero_and_age():
    repo = Path(__file__).resolve().parents[1]
    script = repo / "bin" / "mqtop"
    mod = runpy.run_path(str(script))

    now = 1000
    jobs = [
        {
            "id": "1",
            "name": "same",
            "walltime_used": 5,
            "walltime_total": 20,
            "ncpus": 1,
            "mem_request_gb": 1,
            "state": "R",
            "queue": "cpu",
            "start_time": 900,
            "qtime": 900,
        },
        {
            "id": "2",
            "name": "fin",
            "walltime_used": 10,
            "walltime_total": 20,
            "ncpus": 1,
            "mem_request_gb": 1,
            "state": "C",
            "queue": "cpu",
            "obittime": 900,
        },
    ]

    lines, _, rows = mod["format_jobs"](jobs, now=now, return_rows=True)
    assert rows[0]["waited"] == "00:00"
    assert rows[0]["age"] == ""
    assert rows[1]["age"] != ""


def test_sort_jobs_order_and_toggle():
    repo = Path(__file__).resolve().parents[1]
    script = repo / "bin" / "mqtop"
    mod = runpy.run_path(str(script))

    now = 1000
    jobs = [
        {"id": "r1", "state": "R", "walltime_used": 50, "queue": "cpu"},
        {"id": "r2", "state": "R", "walltime_used": 10, "queue": "cpu"},
        {"id": "q1", "state": "Q", "qtime": 800, "queue": "cpu"},
        {"id": "q2", "state": "Q", "qtime": 900, "queue": "cpu"},
        {"id": "f1", "state": "C", "obittime": 950, "queue": "cpu"},
        {"id": "f2", "state": "C", "obittime": 900, "queue": "cpu"},
    ]

    ordered = mod["sort_jobs"](jobs, now=now, show_queued=True)
    assert [j["id"] for j in ordered] == ["r1", "r2", "q1", "q2", "f1", "f2"]

    ordered_noq = mod["sort_jobs"](jobs, now=now, show_queued=False)
    assert [j["id"] for j in ordered_noq] == ["r1", "r2", "f1", "f2"]

