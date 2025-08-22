import subprocess
import sys
import re
from pathlib import Path

ANSI = re.compile(r"\x1b\[[0-9;]*m")

def split_cols(line):
    line = ANSI.sub('', line.rstrip())
    return re.split(r"\s{2,}", line)

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
    lines = result.stdout.rstrip().splitlines()
    assert len(lines) == 5
    header = split_cols(lines[0])
    assert header == [
        "job_id",
        "name",
        "time used",
        "progress",
        "walltime",
        "CPU",
        "RAM(G)",
        "queue",
    ]
    rows = [split_cols(line) for line in lines[1:]]

    # testjob
    assert rows[0][0] == "123.server"
    assert rows[0][1] == "testjob"
    assert rows[0][2] == "00:10"
    assert rows[0][4] == "01:00"
    assert rows[0][5] == "4"
    assert rows[0][6] == "4"
    assert rows[0][7] == "batch"
    assert "\x1b[92m" in lines[1]  # green progress

    def no_icon(val):
        return val.rstrip('💪🧠')

    # bigmem with high RAM icon and queue truncation
    assert rows[1][0] == "456.server"
    assert rows[1][5] == "8"
    assert no_icon(rows[1][6]) == "256"
    assert rows[1][7] == "test"
    assert "🧠" in lines[2]
    assert "\x1b[92m" in lines[2]

    # bigcpu with high CPU icon
    assert rows[2][0] == "789.server"
    assert no_icon(rows[2][5]) == "32"
    assert rows[2][6] == "64"
    assert rows[2][7] == "batch"
    assert "💪" in lines[3]
    assert "\x1b[92m" in lines[3]

    # almostdone with red progress bar
    assert rows[3][0] == "222.server"
    assert rows[3][5] == "2"
    assert rows[3][6] == "2"
    assert rows[3][7] == "batch"
    assert "\x1b[91m" in lines[4]

    # ensure interactive job was filtered out
    assert all("cpu_inter_exec" not in line for line in lines)
