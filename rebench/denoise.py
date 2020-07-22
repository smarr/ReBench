from __future__ import print_function

import json
import sys

from argparse import ArgumentParser
from enum import Enum
from cpuinfo import get_cpu_info

try:
    from . import __version__ as rebench_version
except ValueError:
    rebench_version = "unknown"


class ScalingGovernors(Enum):
    """For intel_pstate systems, there's only powersave and performance"""
    POWERSAVE = "powersave"
    PERFORMANCE = "performance"


def set_scaling_governor(governor):
    cpu_info = get_cpu_info()
    num_cores = cpu_info["count"]
    assert governor in (ScalingGovernors.POWERSAVE, ScalingGovernors.PERFORMANCE),\
        "The scaling governor is expected to be performance or powersave, but was " + governor

    try:
        for cpu_i in range(num_cores):
            filename = "/sys/devices/system/cpu/cpu" + str(cpu_i) + "/cpufreq/scaling_governor"
            with open(filename, "w") as gov_file:
                gov_file.write(governor + "\n")
    except IOError:
        return "failed"

    return governor


def set_no_turbo(with_no_turbo):
    if with_no_turbo:
        value = "1"
    else:
        value = "0"

    try:
        with open("/sys/devices/system/cpu/intel_pstate/no_turbo", "w") as nt_file:
            nt_file.write(value + "\n")
    except IOError:
        return "failed"
    return with_no_turbo


def minimize_perf_sampling():
    try:
        with open("/proc/sys/kernel/perf_cpu_time_max_percent", "w") as perc_file:
            perc_file.write("1\n")

        with open("/proc/sys/kernel/perf_event_max_sample_rate", "w") as sample_file:
            sample_file.write("1\n")
    except IOError:
        return "failed"

    return "1"


def restore_perf_sampling():
    try:
        with open("/proc/sys/kernel/perf_cpu_time_max_percent", "w") as perc_file:
            perc_file.write("25\n")
    except IOError:
        return "failed"
    return "restored"


def minimize_noise():
    governor = set_scaling_governor(ScalingGovernors.PERFORMANCE)
    no_turbo = set_no_turbo(True)
    perf = minimize_perf_sampling()
    return {"scaling_governor": governor,
            "no_turbo": no_turbo,
            "perf_event_max_sample_rate": perf}


def restore_standard_settings():
    governor = set_scaling_governor(ScalingGovernors.POWERSAVE)
    no_turbo = set_no_turbo(False)
    perf = restore_perf_sampling()
    return {"scaling_governor": governor,
            "no_turbo": no_turbo,
            "perf_event_max_sample_rate": perf}


def shell_options():
    parser = ArgumentParser()
    parser.add_argument('--version', action='version',
                        version="%(prog)s " + rebench_version)
    parser.add_argument('--json', action='store_true', default=False,
                        help='Output results as JSON for processing')
    parser.add_argument('command',
                        help=("Either set system to 'minimize' noise or 'restore' " +
                              "the settings assumed to be the original ones"),
                        default=None)
    return parser


def main_func():
    arg_parser = shell_options()
    args = arg_parser.parse_args()

    if args.command == 'minimize':
        result = minimize_noise()
    elif args.command == 'restore':
        result = restore_standard_settings()
    else:
        arg_parser.print_help()
        return -1

    if args.json:
        print(json.dumps(result))
    else:
        print("Setting scaling_governor:           ", result["scaling_governor"])
        print("Setting no_turbo:                   ", result["no_turbo"])
        print("Setting perf_event_max_sample_rate: ", result["perf_event_max_sample_rate"])

    if "failed" in result.values():
        return -1
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main_func())
