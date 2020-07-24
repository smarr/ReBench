from __future__ import print_function

import getpass
import json
import os
import subprocess
import sys

from argparse import ArgumentParser
from math import log, floor
from cpuinfo import get_cpu_info

from .subprocess_with_timeout import output_as_str

try:
    from . import __version__ as rebench_version
except ValueError:
    rebench_version = "unknown"


class DenoiseResult(object):

    def __init__(self, succeeded, warn_msg, use_nice, use_shielding, details):
        self.succeeded = succeeded
        self.warn_msg = warn_msg
        self.use_nice = use_nice
        self.use_shielding = use_shielding
        self.details = details


def minimize_noise(show_warnings, ui):
    result = {}

    try:
        output = output_as_str(subprocess.check_output(
            ['sudo', '-n', 'rebench-denoise', '--json', 'minimize'],
            stderr=subprocess.STDOUT))
        try:
            result = json.loads(output)
            got_json = True
        except ValueError:
            got_json = False
    except subprocess.CalledProcessError as e:
        output = output_as_str(e.output)
        got_json = False

    msg = 'Minimizing noise with rebench-denoise failed\n'
    msg += '{ind}possibly causing benchmark results to vary more.\n\n'

    success = False
    use_nice = False
    use_shielding = False

    if got_json:

        failed = ''

        for k, value in result.items():
            if value == "failed":
                failed += '{ind}{ind} - ' + k + '\n'

        if failed:
            msg += '{ind}Failed to set:\n' + failed + '\n'

        use_nice = result.get("can_set_nice", False)
        use_shielding = result.get("shielding", False)

        if not use_nice and show_warnings:
            msg += ("{ind}Process niceness could not be set.\n"
                    + "{ind}{ind}`nice` is used to elevate the priority of the benchmark,\n"
                    + "{ind}{ind}without it, other processes my interfere with it"
                    + " nondeterministically.\n")

        if not use_shielding and show_warnings:
            msg += ("{ind}Core shielding could not be set up.\n"
                    + "{ind}{ind}Shielding is used to restrict the use of cores to"
                    + " benchmarking.\n"
                    + "{ind}{ind}Without it, there my be more nondeterministic interference.\n")

        if use_nice and use_shielding and not failed:
            success = True
    else:
        if 'password is required' in output:
            try:
                denoise_cmd = output_as_str(subprocess.check_output('which rebench-denoise',
                                                                    shell=True))
            except subprocess.CalledProcessError:
                denoise_cmd = '$PATH_TO/rebench-denoise'

            msg += '{ind}Please make sure `sudo rebench-denoise`'\
                   + ' can be used without password.\n'
            msg += '{ind}To be able to run rebench-denoise without password,\n'
            msg += '{ind}add the following to the end of your sudoers file (using visudo):\n'
            msg += '{ind}{ind}' + getpass.getuser() + ' ALL = (root) NOPASSWD: '\
                   + denoise_cmd + '\n'
        elif 'command not found' in output:
            msg += '{ind}Please make sure `rebench-denoise` is on the PATH\n'
        else:
            msg += '{ind}Error: ' + output

    if not success and show_warnings:
        ui.warning(msg)

    return DenoiseResult(success, msg, use_nice, use_shielding, result)


def restore_noise(denoise_result, show_warning, ui):
    if not denoise_result:
        # likely has failed completely. And without details, just no-op
        return

    values = set(denoise_result.details.values())
    if len(values) == 1 and "failed" in values:
        # everything failed, don't need to try to restore things
        pass
    else:
        try:
            cmd = ['sudo', '-n', 'rebench-denoise', '--json']
            if not denoise_result.use_shielding:
                cmd += ['--without-shielding']
            if not denoise_result.use_nice:
                cmd += ['--without-nice']
            subprocess.check_output(cmd + ['restore'], stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            pass

    if not denoise_result.succeeded and show_warning:
        # warn a second time at the end of the execution
        ui.error(denoise_result.warn_msg)


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
        return core_spec

    return False


def _reset_shielding():
    try:
        output = subprocess.check_output(["cset", "shield", "-r"],
                                         stderr=subprocess.STDOUT)
        output = output_as_str(output)
        return "cset: done" in output
    except OSError:
        return False
    except subprocess.CalledProcessError:
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

    return 1


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
    shielding = _reset_shielding() if use_shielding else False

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


def _shell_options():
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
    arg_parser = _shell_options()
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
