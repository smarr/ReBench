#!/usr/bin/env python3
from os.path import isfile

_CPU_DIR = "/sys/devices/system/cpu"


def read_current_core():
    # /proc/self/stat
    # item 39 (index 38): processor %d
    # item 2 which is in parentheses, may have spaces, so split after
    with open("/proc/self/stat", "r", encoding="utf-8") as stat_file:
        content = stat_file.read()
        after_cmd = content.rsplit(")", 1)[1]
        fields = after_cmd.split()
    return int(fields[38 - 2])


def read_scaling_governor(core):
    filename = f"{_CPU_DIR}/cpu{core}/cpufreq/scaling_governor"
    if not isfile(filename):
        return "unknown"
    with open(filename, "r", encoding="utf-8") as f:
        return f.read().strip()


current_core = read_current_core()
print("Benchmark Core: ", current_core)
print("Benchmark Scaling Governor: ", read_scaling_governor(current_core))
print("RESULT-total: 1000.0")
