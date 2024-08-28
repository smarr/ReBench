import json
import os
import subprocess
import sys

from argparse import ArgumentParser
from math import log, floor
from multiprocessing import Pool

from .output import output_as_str, UIError
from .subprocess_kill import kill_process

try:
    from . import __version__ as rebench_version
except ValueError:
    rebench_version = "unknown"


class CommandsPaths:
    """Hold the path information for commands."""

    def __init__(self):
        self._cset_path = None
        self._denoise_path = None
        self._which_path = None
        self._denoise_python_path = None

    def get_which(self):
        if not self._which_path:
            if os.path.isfile('/usr/bin/which'):
                self._which_path = '/usr/bin/which'
            else:
                raise UIError("The basic `which` command was not found." +
                              " In many systems it is available at /usr/bin/which." +
                              " If it is elsewhere rebench-denoise will need to be" +
                              " adapted to support a different location.\n", None)

        return self._which_path

    def _absolute_path_for_command(self, command, arguments_for_successful_exe):
        """
        Find and return the canonical absolute path to make sudo happy.
        If the command is not found or does not execute successfully, return None.
        """
        try:
            selected_cmd = output_as_str(
                subprocess.check_output(
                    [self.get_which(), command],
                    shell=False, stderr=subprocess.DEVNULL)).strip()
            result_cmd = os.path.realpath(selected_cmd)
        except subprocess.CalledProcessError:
            result_cmd = command

        try:
            subprocess.check_output(
                    [result_cmd] + arguments_for_successful_exe,
                    shell=False, stderr=subprocess.DEVNULL)
            return result_cmd
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def has_cset(self):
        if self._cset_path is None:
            self._cset_path = self._absolute_path_for_command('cset', ['--help'])

        return self._cset_path is not None and self._cset_path is not False

    def get_cset(self):
        return self._cset_path

    def set_cset(self, cset_path):
        self._cset_path = cset_path

    def has_denoise(self):
        if self._denoise_path is None:
            self._denoise_path = self._absolute_path_for_command('rebench-denoise', ['--version'])

        return self._denoise_path is not None and self._denoise_path is not False

    def get_denoise(self):
        if not self.has_denoise():
            raise UIError("rebench-denoise not found. " +
                          "Was ReBench installed so that `rebench` and `rebench-denoise` " +
                          "are on the PATH? Python's bin directory for packages " +
                          "may need to be added to PATH manually.\n\n" +
                          "To use ReBench without rebench-denoise, use the --no-denoise option.\n",
                          None)

        return self._denoise_path

    def get_denoise_python_path(self):
        if self._denoise_python_path is None:
            active_python_path = sys.path
            current_file = os.path.abspath(__file__)

            # find the element in active_python_path that has the start of the current file path
            for path in active_python_path:
                if current_file.startswith(path) and 'rebench' in path.lower():
                    self._denoise_python_path = path
                    return path

            self._denoise_python_path = False

        return self._denoise_python_path


paths = CommandsPaths()


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


def _shield_lower_bound(num_cores):
    return int(floor(log(num_cores)))


def _shield_upper_bound(num_cores):
    return num_cores - 1


def _activate_shielding(num_cores, shield):
    if shield:
        core_spec = shield
    else:
        min_cores = _shield_lower_bound(num_cores)
        max_cores = _shield_upper_bound(num_cores)
        core_spec = "%d-%d" % (min_cores, max_cores)

    if not paths.has_cset():
        return False

    try:
        output = subprocess.check_output([paths.get_cset(), "shield", "-c", core_spec, "-k", "on"],
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
        output = subprocess.check_output([paths.get_cset(), "shield", "-r"],
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
            with open(filename, "w") as gov_file:  # pylint: disable=unspecified-encoding
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
        # pylint: disable-next=unspecified-encoding
        with open("/sys/devices/system/cpu/intel_pstate/no_turbo", "w") as nt_file:
            nt_file.write(value + "\n")
    except IOError:
        return "failed"
    return with_no_turbo


def _configure_perf_sampling(for_profiling):
    try:
        # pylint: disable-next=unspecified-encoding
        with open("/proc/sys/kernel/perf_cpu_time_max_percent", "w") as perc_file:
            if for_profiling:
                perc_file.write("0\n")
            else:
                perc_file.write("1\n")

        # pylint: disable-next=unspecified-encoding
        with open("/proc/sys/kernel/perf_event_max_sample_rate", "w") as sample_file:
            # for profiling we just disabled it above, and then don't need to set it
            if not for_profiling:
                sample_file.write("1\n")

        if for_profiling:
            # pylint: disable-next=unspecified-encoding
            with open("/proc/sys/kernel/perf_event_paranoid", "w") as perf_file:
                perf_file.write("-1\n")
    except IOError:
        return "failed"

    if for_profiling:
        return 0
    else:
        return 1


def _restore_perf_sampling():
    try:
        # pylint: disable-next=unspecified-encoding
        with open("/proc/sys/kernel/perf_cpu_time_max_percent", "w") as perc_file:
            perc_file.write("25\n")

        # pylint: disable-next=unspecified-encoding
        with open("/proc/sys/kernel/perf_event_max_sample_rate", "w") as sample_file:
            sample_file.write("50000\n")

        # pylint: disable-next=unspecified-encoding
        with open("/proc/sys/kernel/perf_event_paranoid", "w") as perf_file:
            perf_file.write("3\n")
    except IOError:
        return "failed"
    return "restored"


def _minimize_noise(num_cores, use_nice, use_shielding, for_profiling, shield):
    governor = _set_scaling_governor(SCALING_GOVERNOR_PERFORMANCE, num_cores)
    no_turbo = _set_no_turbo(True)
    perf = _configure_perf_sampling(for_profiling)

    can_nice = _can_set_niceness() if use_nice else False
    shielding = _activate_shielding(num_cores, shield) if use_shielding else False

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


def _exec(num_cores, use_nice, use_shielding, args):
    cmdline = []
    if use_shielding and paths.has_cset():
        cmdline += [paths.get_cset(), "shield", "--exec", "--"]
    if use_nice:
        cmdline += ["nice", "-n-20"]
    cmdline += args

    # the first element of cmdline is ignored as argument, since it's the file argument, too
    cmd = cmdline[0]

    # communicate the used core spec to executed command as part of its environment
    env = os.environ.copy()
    if use_shielding and paths.has_cset():
        min_cores = _shield_lower_bound(num_cores)
        max_cores = _shield_upper_bound(num_cores)
        core_spec = "%d-%d" % (min_cores, max_cores)
        env['REBENCH_DENOISE_CORE_SET'] = core_spec

    os.execvpe(cmd, cmdline, env)


def _kill(proc_id):
    kill_process(int(proc_id), True, None, None)


def _calculate(core_id):
    print("Started calculating: %d" % core_id)
    try:
        val = 0
        for _ in range(1, 1000):
            for i in range(1, 1000000):
                val *= i * i / i + i - i
    except KeyboardInterrupt:
        pass
    print("Finished calculating: %d" % core_id)


def _test(num_cores):
    lower = _shield_lower_bound(num_cores)
    upper = _shield_upper_bound(num_cores)
    core_cnt = upper - lower + 1
    pool = Pool(core_cnt)  # pylint: disable=consider-using-with

    print("Test on %d cores" % core_cnt)

    core_spec = "%d-%d" % (lower, upper)
    env_spec = os.environ.get('REBENCH_DENOISE_CORE_SET', None)
    if core_spec != env_spec:
        print("Core Spec set by denoise was: ", env_spec)
        print("Locally determined one was: ", core_spec)
        print("The specs did not match!")

    try:
        pool.map(_calculate, range(0, core_cnt))
    except KeyboardInterrupt:
        pass

    print("exit main")
    pool.terminate()
    print("Done testing on %d cores" % core_cnt)


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
    parser.add_argument('--for-profiling', action='store_true', default=False,
                        dest='for_profiling', help="Don't restrict CPU usage by profiler")
    parser.add_argument('--cset-path', help="Absolute path to cset", default=None)
    parser.add_argument('--num-cores', help="Number of cores. Is required.", default=None)
    parser.add_argument('--shield', help='list of cores to shield, e.g. 0-3,5,12-43',
                        action='store', default=None, dest='shield')
    parser.add_argument('command',
                        help=("`minimize`|`restore`|`exec -- `|`kill pid`|`test`: "
                              "`minimize` sets system to reduce noise. " +
                              "`restore` sets system to the assumed original settings. " +
                              "`exec -- ` executes the given arguments. " +
                              "`kill pid` send kill signal to the process with given id " +
                              "and all child processes. " +
                              "`test` executes a computation for 20 seconds in parallel. " +
                              "it is only useful to test rebench-denoise itself."),
                        default=None)
    return parser


EXIT_CODE_SUCCESS = 0
EXIT_CODE_CHANGING_SETTINGS_FAILED = 1
EXIT_CODE_NUM_CORES_UNSET = 2
EXIT_CODE_NO_COMMAND_SELECTED = 3


def main_func():
    arg_parser = _shell_options()
    args, remaining_args = arg_parser.parse_known_args()

    paths.set_cset(args.cset_path)

    num_cores = int(args.num_cores) if args.num_cores else None
    result = {}

    if args.command == 'minimize' and num_cores is not None:
        result = _minimize_noise(num_cores, args.use_nice, args.use_shielding, args.for_profiling,
                                 args.shield)
    elif args.command == 'restore' and num_cores is not None:
        result = _restore_standard_settings(num_cores, args.use_shielding)
    elif args.command == 'exec':
        _exec(num_cores, args.use_nice, args.use_shielding, remaining_args)
    elif args.command == 'kill':
        _kill(remaining_args[0])
    elif args.command == 'test' and num_cores is not None:
        _test(num_cores)
    else:
        arg_parser.print_help()
        if num_cores is None:
            print("The --num-cores must be provided.")
            return EXIT_CODE_NUM_CORES_UNSET
        return EXIT_CODE_NO_COMMAND_SELECTED

    if args.json:
        print(json.dumps(result))
    else:
        print("Setting scaling_governor:           ", result.get("scaling_governor", None))
        print("Setting no_turbo:                   ", result.get("no_turbo", False))
        print("Setting perf_event_max_sample_rate: ",
              result.get("perf_event_max_sample_rate", None))
        print("")
        print("Enabled core shielding:             ", result.get("shielding", False))
        print("")
        print("Can set niceness:                   ", result.get("can_set_nice", False))

    if "failed" in result.values():
        return EXIT_CODE_CHANGING_SETTINGS_FAILED
    else:
        return EXIT_CODE_SUCCESS


if __name__ == "__main__":
    sys.exit(main_func())
