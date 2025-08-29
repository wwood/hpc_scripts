import subprocess
import sys
import re
from pathlib import Path

ANSI = re.compile(r"\x1b\[[0-9;]*m")

def split_cols(line):
    line = ANSI.sub('', line.rstrip('\n'))
    parts = re.split(r"\s{2,}", line)
    return [p.strip() for p in parts]

def test_mqtop_print_first_page():
    repo = Path(__file__).resolve().parents[1]
    script = repo / "bin" / "mqtop"
    qstat_file = repo / "tests" / "data" / "qstat_f.txt"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--print-first-page",
            "--qstat-f-file",
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
    ]
    assert "222.server" in lines[1]
    assert "almostdone" in lines[1]
    assert "  2" in lines[1]
    assert "R      batch" in lines[1]
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
    lines, _ = mod["format_jobs"](jobs)
    header, row_plain, row_emoji = [ANSI.sub("", l) for l in lines[:3]]
    q_idx = display_index(header, "queue")
    assert display_index(row_plain, "batch") == q_idx
    assert display_index(row_emoji, "batch") == q_idx


def test_mqtop_history_only_print_first_page():
    repo = Path(__file__).resolve().parents[1]
    script = repo / "bin" / "mqtop"
    qstat_f = repo / "tests" / "data" / "qstat_f_empty.txt"
    qstat_xf = repo / "tests" / "data" / "qstat_xf_finished.txt"
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--print-first-page",
            "--qstat-f-file",
            str(qstat_f),
            "--qstat-xf-file",
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
    ]
    assert "10592488" in lines[1]
    assert "🐍semibin.23.sh" in lines[1]
    assert lines.count(lines[0]) == 1


def test_mqtop_print_first_page_warning(capsys):
    repo = Path(__file__).resolve().parents[1]
    script = repo / "bin" / "mqtop"
    import runpy, sys
    mod = runpy.run_path(str(script))

    def fake_parse_qstat(path=None, include_history=False, max_jobs=None):
        mod['mqstat'].parse_qstat.limit_hit = True
        mod['mqstat'].parse_qstat.hist_limit_hit = True
        return [
            {
                "id": "1.server",
                "name": "job",
                "state": "R",
                "queue": "batch",
                "ncpus": 1,
                "mem_request_gb": 1,
                "walltime_used": 0,
                "walltime_total": 0,
            }
        ]

    mod['mqstat'].parse_qstat = fake_parse_qstat
    orig_argv = sys.argv
    sys.argv = ["mqtop", "--print-first-page"]
    try:
        mod['main']()
    finally:
        sys.argv = orig_argv
    lines = [ANSI.sub("", l) for l in capsys.readouterr().out.splitlines() if l]
    assert lines[0].startswith("WARNING: qstat -f")
    assert lines[1].startswith("WARNING: qstat -xf")
