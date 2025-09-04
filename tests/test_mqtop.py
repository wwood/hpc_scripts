import subprocess
import sys
import re
import pstats
from pathlib import Path

ANSI = re.compile(r"\x1b\[[0-9;]*m")


def split_cols(line):
    line = ANSI.sub("", line.rstrip("\n"))
    parts = re.split(r"\s{2,}", line)
    return [p.strip() for p in parts]


def test_mqtop_print_first_page():
    repo = Path(__file__).resolve().parents[1]
    script = repo / "bin" / "mqtop"
    qstat_file = repo / "tests" / "data" / "qstat.json"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--print-first-page",
            "--qstat-json",
            str(qstat_file),
        ],
        text=True,
        capture_output=True,
        check=True,
    )
    lines = result.stdout.splitlines()
    assert len(lines) == 5
    header = [c for c in split_cols(lines[0]) if c]
    assert header == [
        "job_id",
        "name",
        "time used",
        "progress",
        "walltime",
        "waited",
        "age",
        "CPU",
        "cpu%",
        "RAM(G)",
        "ram%",
        "state",
        "queue",
        "note",
        "source",
    ]
    assert "222.server" in lines[1]
    assert "almostdone" in lines[1]
    assert "  2" in lines[1]
    assert "R      batch" in lines[1]
    assert split_cols(lines[1])[-1] == "qstat.json"
    assert "123.server" in lines[-1]


def test_mqtop_alignment_wide_chars():
    repo = Path(__file__).resolve().parents[1]
    script = repo / "bin" / "mqtop"
    import runpy, unicodedata

    def width(ch):
        if unicodedata.combining(ch):
            return 0
        return 2 if unicodedata.east_asian_width(ch) in ("F", "W") else 1

    def display_index(line, text):
        idx = line.index(text)
        return sum(width(ch) for ch in line[:idx])

    mod = runpy.run_path(str(script))
    jobs = [
        {
            "id": "1.server",
            "name": "test",
            "queue": "batch",
            "state": "R",
            "ncpus": 1,
            "mem_request_gb": 1,
            "walltime_used": 0,
            "walltime_total": 0,
        },
        {
            "id": "2.server",
            "name": "🐍test",
            "queue": "batch",
            "state": "R",
            "ncpus": 1,
            "mem_request_gb": 1,
            "walltime_used": 0,
            "walltime_total": 0,
        },
    ]
    lines, _ = mod["format_jobs"](jobs, 200)
    header, row_plain, row_emoji = [ANSI.sub("", l) for l in lines[:3]]
    q_idx = display_index(header, "queue")
    assert display_index(row_plain, "batch") == q_idx
    assert display_index(row_emoji, "batch") == q_idx


def test_mqtop_history_only_print_first_page():
    repo = Path(__file__).resolve().parents[1]
    script = repo / "bin" / "mqtop"
    qstat_f = repo / "tests" / "data" / "qstat_empty.json"
    qstat_xf = repo / "tests" / "data" / "qstatx_finished.json"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--print-first-page",
            "--qstat-json",
            str(qstat_f),
            "--qstatx-json",
            str(qstat_xf),
        ],
        text=True,
        capture_output=True,
        check=True,
    )
    lines = [l for l in result.stdout.splitlines() if l]
    assert len(lines) == 2
    header = [c for c in split_cols(lines[0]) if c]
    assert header == [
        "job_id",
        "name",
        "time used",
        "progress",
        "walltime",
        "waited",
        "age",
        "CPU",
        "cpu%",
        "RAM(G)",
        "ram%",
        "state",
        "queue",
        "note",
        "source",
    ]
    assert "10592488" in lines[1]
    assert "🐍semibin.23.sh" in lines[1]
    assert split_cols(lines[1])[-1] == "qstatx.json"
    assert lines.count(lines[0]) == 1


def test_mqtop_updates_recent_finished_job():
    import runpy, io, contextlib, json

    repo = Path(__file__).resolve().parents[1]
    script = repo / "bin" / "mqtop"
    qstat_f = repo / "tests" / "data" / "qstat_empty.json"
    qstat_x = repo / "tests" / "data" / "qstatx_running.json"
    mod = runpy.run_path(str(script))
    calls = []

    def fake_fetch(jid, user):
        calls.append(jid)
        with open(repo / "tests" / "data" / "qstatx_finished.json") as fh:
            data = json.load(fh)
        info = data["Jobs"][jid]
        info["id"] = jid
        return mod["_parse_job"](info)

    globs = mod["main"].__globals__
    globs["_fetch_job"] = fake_fetch
    globs["_recent_finished_jobs"] = lambda u, e: ([], 0, 0)

    sys.argv = [
        "mqtop",
        "--print-first-page",
        "--qstat-json",
        str(qstat_f),
        "--qstatx-json",
        str(qstat_x),
    ]

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        mod["main"]()
    lines = [l for l in buf.getvalue().splitlines() if l]
    assert len(lines) == 2
    header = [c for c in split_cols(lines[0]) if c]
    row = split_cols(lines[1])
    while len(row) < len(header):
        if len(row) <= header.index("age"):
            row.insert(header.index("age"), "")
        else:
            row.insert(header.index("note"), "")
    assert row[0] == "10592488"
    assert row[header.index("state")] == "F"
    assert row[header.index("source")] == "qstatx.json"
    assert calls == ["10592488.aqua"]


def test_mqtop_deduplicates_overlapping_jobs():
    repo = Path(__file__).resolve().parents[1]
    script = repo / "bin" / "mqtop"
    qstat_f = repo / "tests" / "data" / "qstat.json"
    qstat_x = repo / "tests" / "data" / "qstatx_duplicate.json"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--print-first-page",
            "--qstat-json",
            str(qstat_f),
            "--qstatx-json",
            str(qstat_x),
        ],
        text=True,
        capture_output=True,
        check=True,
    )
    lines = [l for l in result.stdout.splitlines() if l]
    assert len(lines) == 5
    assert sum("123.server" in l for l in lines) == 1
    row = next(l for l in lines if "123.server" in l)
    cols = [c for c in split_cols(row) if c]
    assert cols[0] == "123.server"
    assert cols[-3] == "R"
    assert cols[-2] == "batch"
    assert cols[-1] == "qstat.json"


def test_mqtop_reports_qselect_stats():
    import runpy, io, contextlib, json

    repo = Path(__file__).resolve().parents[1]
    script = repo / "bin" / "mqtop"
    qstat_empty = repo / "tests" / "data" / "qstat_empty.json"
    mod = runpy.run_path(str(script))

    with open(repo / "tests" / "data" / "qstatx_finished.json") as fh:
        data = json.load(fh)
    jid, info = next(iter(data["Jobs"].items()))
    info["id"] = jid
    job = mod["_parse_job"](info)
    job["source"] = "qselect/qstat -f"

    globs = mod["main"].__globals__
    globs["_recent_finished_jobs"] = lambda u, e: ([job], 3, 1)

    sys.argv = [
        "mqtop",
        "--print-first-page",
        "--qstat-json",
        str(qstat_empty),
        "--qstatx-json",
        str(qstat_empty),
    ]

    buf_out = io.StringIO()
    buf_err = io.StringIO()
    with contextlib.redirect_stdout(buf_out), contextlib.redirect_stderr(buf_err):
        mod["main"]()

    lines = [l for l in buf_out.getvalue().splitlines() if l]
    assert "qselect detected 3 jobs; updated 1" in buf_err.getvalue()
    header = [c for c in split_cols(lines[0]) if c]
    row = split_cols(lines[1])
    while len(row) < len(header):
        if len(row) <= header.index("age"):
            row.insert(header.index("age"), "")
        else:
            row.insert(header.index("note"), "")
    assert row[0] == jid.split(".")[0]
    assert row[header.index("source")] == "qselect/qstat -f"


def test_history_loader_runs_in_background():
    import runpy, time

    repo = Path(__file__).resolve().parents[1]
    script = repo / "bin" / "mqtop"
    mod = runpy.run_path(str(script))

    calls = []

    def fake_load(path, user, source):
        time.sleep(0.2)
        calls.append(("load", source))
        return [{"id": "1", "state": "F", "source": source}]

    def fake_recent(user, existing):
        calls.append(("recent", len(existing)))
        return [], 0, 0

    globs = mod["_start_history_loader"].__globals__
    globs["_load_jobs_from_json"] = fake_load
    globs["_recent_finished_jobs"] = fake_recent

    thread, result = mod["_start_history_loader"]("dummy", "user", {"2"})
    assert thread.is_alive()
    thread.join()
    assert result == {"1": {"id": "1", "state": "F", "source": "qstatx.json"}}
    assert calls == [("load", "qstatx.json"), ("recent", 2)]


def test_mqtop_profile(tmp_path):
    repo = Path(__file__).resolve().parents[1]
    script = repo / "bin" / "mqtop"
    qstat_file = repo / "tests" / "data" / "qstat.json"
    prof = tmp_path / "stats.prof"
    subprocess.run(
        [
            sys.executable,
            str(script),
            "--print-first-page",
            "--qstat-json",
            str(qstat_file),
            "--profile",
            str(prof),
        ],
        text=True,
        capture_output=True,
        check=True,
    )
    assert prof.exists()
    stats = pstats.Stats(str(prof))
    assert any("get_jobs" in func for (_, _, func) in stats.stats)


def test_view_log_command_checks_running(tmp_path):
    import runpy

    repo = Path(__file__).resolve().parents[1]
    script = repo / "bin" / "mqtop"
    mod = runpy.run_path(str(script))

    job = {"id": "123.server", "state": "R"}

    logdir = tmp_path
    stderr_file = logdir / f"{job['id']}.ER"
    stderr_file.write_text("err")

    mod["mqsub"].PbsJobInfo.stdout_and_stderr_paths = staticmethod(
        lambda jid, segregated_logs_dir=None: (str(logdir), str(logdir))
    )

    calls = []

    def fake_fetch(jid, user):
        calls.append(jid)
        return {"id": jid, "state": "F"}

    mod["_fetch_job"] = fake_fetch
    mod["_view_log_command"].__globals__["_fetch_job"] = fake_fetch

    cmd, shell = mod["_view_log_command"](job, "e", "user")

    assert calls == ["123.server"]
    assert job["state"] == "F"
    assert shell is False
    assert cmd == ["less", str(stderr_file)]

