from __future__ import print_function

import json
import os
import subprocess
import sys

from argparse import ArgumentParser
from math import log, floor
from cpuinfo import get_cpu_info

try:
    from . import __version__ as rebench_version
except ValueError:
    rebench_version = "unknown"


def output_as_str(string_like):
    if type(string_like) != str:  # pylint: disable=unidiomatic-typecheck
        return string_like.decode('utf-8')
    else:
        return string_like


def _can_set_niceness():
    """
    Check whether we can ask the operating system to influence the priority of
    our benchmarks.
    """
    try:
        output = subprocess.check_output(["nice", "-n-20", "echo", "test"],
                                         stderr=subprocess.STDOUT)
        output = output_as_str(output)
    except OSError:
        return False

    if "cannot set niceness" in output or "Permission denied" in output:
        return False
    else:
        return True


def _activate_shielding(num_cores):
    min_cores = floor(log(num_cores))
    max_cores = num_cores - 1
    core_spec = "%d-%d" % (min_cores, max_cores)
    try:
        output = subprocess.check_output(["cset", "shield", "-c", core_spec, "-k", "on"],
                                         stderr=subprocess.STDOUT)
        output = output_as_str(output)
    except OSError:
        return False

    if "Permission denied" in output:
        return False

    if "kthread shield activated" in output:
        return True

    return False


def _reset_shielding():
    try:
        output = subprocess.check_output(["cset", "shield", "-r"],
                                         stderr=subprocess.STDOUT)
        output = output_as_str(output)
        return "cset: done" in output
    except OSError:
        return False


# For intel_pstate systems, there's only powersave and performance
SCALING_GOVERNOR_POWERSAVE = "powersave"
SCALING_GOVERNOR_PERFORMANCE = "performance"


def _set_scaling_governor(governor, num_cores):
    assert governor in (SCALING_GOVERNOR_POWERSAVE, SCALING_GOVERNOR_PERFORMANCE),\
        "The scaling governor is expected to be performance or powersave, but was " + governor

    try:
        for cpu_i in range(num_cores):
            filename = "/sys/devices/system/cpu/cpu" + str(cpu_i) + "/cpufreq/scaling_governor"
            with open(filename, "w") as gov_file:
                gov_file.write(governor + "\n")
    except IOError:
        return "failed"

    return governor


def _set_no_turbo(with_no_turbo):
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


def _minimize_perf_sampling():
    try:
        with open("/proc/sys/kernel/perf_cpu_time_max_percent", "w") as perc_file:
            perc_file.write("1\n")

        with open("/proc/sys/kernel/perf_event_max_sample_rate", "w") as sample_file:
            sample_file.write("1\n")
    except IOError:
        return "failed"

    return "1"


def _restore_perf_sampling():
    try:
        with open("/proc/sys/kernel/perf_cpu_time_max_percent", "w") as perc_file:
            perc_file.write("25\n")
    except IOError:
        return "failed"
    return "restored"


def _minimize_noise(num_cores, use_nice, use_shielding):
    governor = _set_scaling_governor(SCALING_GOVERNOR_PERFORMANCE, num_cores)
    no_turbo = _set_no_turbo(True)
    perf = _minimize_perf_sampling()
    can_nice = _can_set_niceness() if use_nice else False
    shielding = _activate_shielding(num_cores) if use_shielding else False

    return {"scaling_governor": governor,
            "no_turbo": no_turbo,
            "perf_event_max_sample_rate": perf,
            "can_set_nice": can_nice,
            "shielding": shielding}


def _restore_standard_settings(num_cores, use_shielding):
    governor = _set_scaling_governor(SCALING_GOVERNOR_POWERSAVE, num_cores)
    no_turbo = _set_no_turbo(False)
    perf = _restore_perf_sampling()

    if use_shielding:
        shielding = _reset_shielding()

    return {"scaling_governor": governor,
            "no_turbo": no_turbo,
            "perf_event_max_sample_rate": perf,
            "shielding": shielding}


def _exec(use_nice, use_shielding, args):
    cmdline = []
    if use_shielding:
        cmdline += ["cset", "shield", "--exec", "--"]
    if use_nice:
        cmdline += ["nice", "-n-20"]
    cmdline += args

    # the first element of cmdline is ignored as argument, since it's the file argument, too
    cmd = cmdline[0]
    os.execvp(cmd, cmdline)


def shell_options():
    parser = ArgumentParser()
    parser.add_argument('--version', action='version',
                        version="%(prog)s " + rebench_version)
    parser.add_argument('--json', action='store_true', default=False,
                        help='Output results as JSON for processing')
    parser.add_argument('--without-nice', action='store_false', default=True,
                        dest='use_nice', help="Don't try setting process niceness")
    parser.add_argument('--without-shielding', action='store_false', default=True,
                        dest='use_shielding', help="Don't try shielding cores")
    parser.add_argument('command',
                        help=("`minimize`|`restore`|`exec -- `: "
                              "`minimize` sets system to reduce noise. "
                              "`restore` sets system to the assumed original settings. " +
                              "`exec -- ` executes the given arguments."),
                        default=None)
    return parser


def main_func():
    arg_parser = shell_options()
    args, remaining_args = arg_parser.parse_known_args()

    cpu_info = get_cpu_info()
    num_cores = cpu_info["count"]

    if args.command == 'minimize':
        result = _minimize_noise(num_cores, args.use_nice, args.use_shielding)
    elif args.command == 'restore':
        result = _restore_standard_settings(num_cores, args.use_shielding)
    elif args.command == 'exec':
        _exec(args.use_nice, args.use_shielding, remaining_args)
    else:
        arg_parser.print_help()
        return -1

    if args.json:
        print(json.dumps(result))
    else:
        print("Setting scaling_governor:           ", result["scaling_governor"])
        print("Setting no_turbo:                   ", result["no_turbo"])
        print("Setting perf_event_max_sample_rate: ", result["perf_event_max_sample_rate"])
        print("")
        print("Enabled core shielding:             ", result.get("shielding", False))
        print("")
        print("Can set niceness:                   ", result.get("can_set_nice", False))

    if "failed" in result.values():
        return -1
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main_func())
