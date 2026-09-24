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


def read_value(filename):
    if not isfile(filename):
        return None
    with open(filename, "r", encoding="utf-8") as f:
        return f.read().strip()


def is_turbo_boost_disabled(core):
    intel_no_turbo = read_value(_CPU_DIR + "/intel_pstate/no_turbo")
    global_boost = read_value(_CPU_DIR + "/cpufreq/boost")
    core_boost = read_value(f"{_CPU_DIR}/cpu{core}/cpufreq/boost")

    if intel_no_turbo is None and global_boost is None and core_boost is None:
        return "unknown"

    return intel_no_turbo == "1" or global_boost == "0" or core_boost == "0"


current_core = read_current_core()
print("Benchmark Core: ", current_core)
print("Benchmark Turbo Boost Disabled: ", is_turbo_boost_disabled(current_core))
print("RESULT-total: 1000.0")
