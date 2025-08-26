import subprocess
import sys
import re
from pathlib import Path

ANSI = re.compile(r"\x1b\[[0-9;]*m")

def split_cols(line):
    line = ANSI.sub('', line.rstrip('\n'))
    parts = re.split(r"\s{2,}", line)
    return [p.strip() for p in parts]

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
    lines = result.stdout.splitlines()
    assert len(lines) == 6
    header = [c for c in split_cols(lines[0]) if c]
    assert header == [
        "job_id",
        "name",
        "time used",
        "progress",
        "walltime",
        "CPU",
        "RAM(G)",
        "state",
        "queue",
        "note",
    ]
    rows = [split_cols(line) for line in lines[1:]]

    # testjob
    assert rows[0][0] == "123.server"
    assert rows[0][1] == "testjob"
    assert rows[0][2] == "00:10"
    assert rows[0][4] == "01:00"
    assert rows[0][5] == "4"
    assert rows[0][6] == "4"
    assert rows[0][7] == "R"
    assert rows[0][8] == "batch"
    assert rows[0][9] == ""
    assert "\x1b[92m" in lines[1]  # green progress

    def no_icon(val):
        return val.rstrip('💪🧠')

    # bigmem with high RAM icon and queue truncation
    assert rows[1][0] == "456.server"
    assert rows[1][5] == "8"
    assert no_icon(rows[1][6]) == "256"
    assert rows[1][7] == "R"
    assert rows[1][8] == "test"
    assert rows[1][9] == ""
    assert "🧠" in lines[2]
    assert "\x1b[92m" in lines[2]

    # bigcpu with high CPU icon
    assert rows[2][0] == "789.server"
    assert no_icon(rows[2][5]) == "64"
    assert rows[2][6] == "64"
    assert rows[2][7] == "R"
    assert rows[2][8] == "batch"
    assert rows[2][9].startswith("❗")
    assert "over-resourced" not in rows[2][9]
    assert "<10% of CPU used" in rows[2][9]
    assert "💪" in lines[3]
    assert "\x1b[92m" in lines[3]

    # almostdone with red progress bar
    assert rows[3][0] == "222.server"
    assert rows[3][5] == "2"
    assert rows[3][6] == "2"
    assert rows[3][7] == "R"
    assert rows[3][8] == "batch"
    assert rows[3][9] == ""
    assert "\x1b[91m" in lines[4]

    # finished job
    assert rows[4][0] == "333.server"
    assert rows[4][7] == "C"
    assert rows[4][8] == "batch"
    assert rows[4][9] == ""

    # ensure interactive job was filtered out
    assert all("cpu_inter_exec" not in line for line in lines)


def test_parse_qstat_finished_usage():
    repo = Path(__file__).resolve().parents[1]
    script = repo / "bin" / "mqstat"
    qstat_file = repo / "tests" / "data" / "qstat_f.txt"
    import runpy
    mod = runpy.run_path(str(script))
    jobs = mod['parse_qstat'](path=str(qstat_file))
    finished = next(j for j in jobs if j['id'] == '333.server')
    assert finished['cput_used'] == 120
    assert finished['vmem_used_kb'] == 100 * 1024
    assert finished['start_time'] - finished['qtime'] == 5 * 60
    assert finished['obittime'] - finished['start_time'] == 10 * 60


def test_parse_qstat_max_jobs():
    repo = Path(__file__).resolve().parents[1]
    script = repo / "bin" / "mqstat"
    import os, runpy
    os.environ.pop("MQSTAT_QSTAT_F", None)
    mod = runpy.run_path(str(script))
    captured = []

    def fake_run_command(cmd):
        captured.append(cmd)
        return "Job Id: 1.server\n"

    mod['parse_qstat'].__globals__['run_command'] = fake_run_command
    mod['parse_qstat'](max_jobs=10, include_history=True)
    assert captured == [
        "qstat -f -t | awk '/Job Id:/{if (count++==10) {print \"AWK_LIMIT_REACHED\"; exit}} {print}'",
        "qstat -xf -t | awk '/Job Id:/{if (count++==10) {print \"AWK_LIMIT_REACHED\"; exit}} {print}'",
    ]


def test_parse_qstat_merges_active_and_history():
    repo = Path(__file__).resolve().parents[1]
    script = repo / "bin" / "mqstat"
    import os, runpy
    os.environ.pop("MQSTAT_QSTAT_F", None)
    mod = runpy.run_path(str(script))

    def fake_run_command(cmd):
        if "qstat -f -t" in cmd:
            return "Job Id: 1.server\nJob Id: 2.server\nAWK_LIMIT_REACHED\n"
        return "Job Id: 2.server\nJob Id: 3.server\n"

    mod['parse_qstat'].__globals__['run_command'] = fake_run_command
    jobs = mod['parse_qstat'](max_jobs=10, include_history=True)
    ids = sorted(j['id'] for j in jobs)
    assert ids == ['1.server', '2.server', '3.server']
    assert mod['parse_qstat'].limit_hit is True


def test_parse_qstat_history_limit_hit():
    repo = Path(__file__).resolve().parents[1]
    script = repo / "bin" / "mqstat"
    import runpy
    mod = runpy.run_path(str(script))

    def fake_run_command(cmd):
        if "qstat -f -t" in cmd:
            return "Job Id: 0.server\n"
        return "Job Id: 1.server\nAWK_LIMIT_REACHED\n"

    mod['parse_qstat'].__globals__['run_command'] = fake_run_command
    jobs = mod['parse_qstat'](max_jobs=1, include_history=True)
    assert len(jobs) == 2
    assert mod['parse_qstat'].limit_hit is False
    assert mod['parse_qstat'].history_limit_hit is True


def test_job_table_history_warning_when_limited():
    repo = Path(__file__).resolve().parents[1]
    script = repo / "bin" / "mqstat"
    import runpy
    mod = runpy.run_path(str(script))
    mod['parse_qstat'].history_limit_hit = True
    job = {
        'id': '1',
        'name': 'a',
        'walltime_used': 10,
        'walltime_total': 20,
        'ncpus': 1,
        'mem_request_gb': 1,
        'state': 'C',
        'queue': 'cpu',
        'cput_used': 10,
        'vmem_used_kb': 1024,
    }
    lines = mod['job_table']([job], finished=True)
    assert lines[0].startswith("\x1b[91mWARNING: job list truncated")
    assert "finished jobs" in lines[0]
    mod['parse_qstat'].history_limit_hit = False


def test_job_table_finished_util_and_note():
    repo = Path(__file__).resolve().parents[1]
    script = repo / "bin" / "mqstat"
    qstat_file = repo / "tests" / "data" / "qstat_f.txt"
    import runpy
    mod = runpy.run_path(str(script))
    jobs = mod['parse_qstat'](path=str(qstat_file))
    finished = next(j for j in jobs if j['id'] == '333.server')
    lines = mod['job_table']([finished], finished=True)
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
        "util(%)",
        "RAM(G)",
        "util(%)",
        "queue",
        "note",
    ]
    row = split_cols(lines[1])
    assert row[0] == "333.server"
    assert row[1] == "finished"
    assert row[5] == "00:05"
    assert row[6] != ""
    assert row[7].rstrip('💪') == "4"
    assert row[8] == "5%"
    assert row[9].rstrip('🧠') == "4"
    assert row[10] == "2%"
    assert row[11] == "batch"
    assert row[12].startswith("!<10% CPU, <10% RAM")
    assert lines[1].count("\x1b[91m") == 2

    raw_header = ANSI.sub('', lines[0])
    raw_row = ANSI.sub('', lines[1])
    cpu_start = raw_header.index("util(%)")
    cpu_field = raw_row[cpu_start:cpu_start + len("util(%)")]
    assert cpu_field == "     5%"
    ram_start = raw_header.find("util(%)", cpu_start + len("util(%)"))
    ram_field = raw_row[ram_start:ram_start + len("util(%)")]
    assert ram_field == "     2%"


def test_job_table_warning_when_limited():
    repo = Path(__file__).resolve().parents[1]
    script = repo / "bin" / "mqstat"
    import runpy
    mod = runpy.run_path(str(script))
    mod['parse_qstat'].limit_hit = True
    job = {'id': '1', 'name': 'a', 'ncpus': 1, 'mem_request_gb': 1, 'state': 'R'}
    lines = mod['job_table']([job])
    assert lines[0].startswith("\x1b[91mWARNING: job list truncated")
    assert "increase --max-jobs" in lines[0]
    mod['parse_qstat'].limit_hit = False


def test_job_table_zero_waited():
    repo = Path(__file__).resolve().parents[1]
    script = repo / "bin" / "mqstat"
    import runpy, time as _time
    mod = runpy.run_path(str(script))
    now = int(_time.time())
    mod['parse_qstat'].limit_hit = False
    job = {
        'id': '1',
        'name': 'immediate',
        'walltime_used': 10,
        'walltime_total': 20,
        'qtime': now,
        'start_time': now,
        'obittime': now,
        'ncpus': 1,
        'mem_request_gb': 1,
        'cput_used': 10,
        'vmem_used_kb': 1024,
        'exit_status': 0,
        'state': 'C'
    }
    lines = mod['job_table']([job], finished=True)
    row = split_cols(lines[1])
    assert row[5] == "00:00"


def test_job_table_running_short_runtime_no_note():
    repo = Path(__file__).resolve().parents[1]
    script = repo / "bin" / "mqstat"
    import runpy
    mod = runpy.run_path(str(script))
    mod['parse_qstat'].limit_hit = False
    job = {
        'id': '1',
        'name': 'short',
        'walltime_used': 60,
        'walltime_total': 120,
        'ncpus': 4,
        'cpupercent': 20,
        'ncpus_used': 4,
        'mem_request_gb': 1,
        'state': 'R'
    }
    lines = mod['job_table']([job])
    row = split_cols(lines[1])
    assert row[-1] == ""


def test_watch_jobs_no_curses_error(monkeypatch):
    repo = Path(__file__).resolve().parents[1]
    script = repo / "bin" / "mqstat"
    import runpy, curses, time
    mod = runpy.run_path(str(script))
    jobs = mod['parse_qstat'](path=str(repo / "tests" / "data" / "qstat_f.txt"))

    def fake_get_jobs(include_history=True):
        return jobs

    class DummyScreen:
        def __init__(self):
            self.calls = 0

        def nodelay(self, flag):
            pass

        def getch(self):
            self.calls += 1
            return -1 if self.calls == 1 else ord('q')

        def getmaxyx(self):
            return (24, 80)

        def addstr(self, *args, **kwargs):
            pass

        def erase(self):
            pass

        def refresh(self):
            pass

    monkeypatch.setattr(curses, 'curs_set', lambda n: None)
    monkeypatch.setattr(curses, 'start_color', lambda: None)
    monkeypatch.setattr(curses, 'use_default_colors', lambda: None)
    monkeypatch.setattr(curses, 'init_pair', lambda *a, **k: None)
    monkeypatch.setattr(curses, 'color_pair', lambda n: 0)
    monkeypatch.setattr(time, 'sleep', lambda x: None)

    def fake_wrapper(func, *args, **kwargs):
        func(DummyScreen())

    monkeypatch.setattr(curses, 'wrapper', fake_wrapper)

    mod['watch_jobs'](fake_get_jobs, interval=0)
