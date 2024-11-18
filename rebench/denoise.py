#!/usr/bin/env python3
import json
import os
import sys

from argparse import ArgumentParser
from math import log, floor
from multiprocessing import Pool
from subprocess import check_output, CalledProcessError, DEVNULL, STDOUT
from typing import Optional, Union, Mapping, Literal

denoise_py = os.path.abspath(__file__)

if __name__ == "__main__":
    # ensure that the rebench module is available
    rebench_module = os.path.dirname(denoise_py)
    sys.path.append(os.path.dirname(rebench_module))

    # pylint: disable-next=import-error
    from output import output_as_str, UIError  # type: ignore

    # pylint: disable-next=import-error
    from subprocess_kill import kill_process  # type: ignore
else:
    from .output import output_as_str, UIError
    from .subprocess_kill import kill_process


class CommandsPaths:
    """Hold the path information for commands."""

    def __init__(self):
        self._cset_path = None
        self._denoise_path = None
        self._which_path = None

    def get_which(self):
        if not self._which_path:
            if os.path.isfile("/usr/bin/which"):
                self._which_path = "/usr/bin/which"
            else:
                raise UIError(
                    "The `which` command was not found."
                    " In many systems it is available at /usr/bin/which."
                    " If it is elsewhere rebench-denoise will need to be"
                    " adapted to support a different location.\n",
                    None,
                )

        return self._which_path

    def _absolute_path_for_command(self, command, arguments_for_successful_exe):
        """
        Find and return the canonical absolute path to make sudo happy.
        If the command is not found or does not execute successfully, return None.
        """
        try:
            selected_cmd = output_as_str(
                check_output([self.get_which(), command], shell=False, stderr=DEVNULL)
            ).strip()
            result_cmd = os.path.realpath(selected_cmd)
        except CalledProcessError:
            result_cmd = command

        try:
            check_output(
                [result_cmd] + arguments_for_successful_exe, shell=False, stderr=DEVNULL
            )
            return result_cmd
        except (CalledProcessError, FileNotFoundError):
            return False

    def has_cset(self):
        if self._cset_path is None:
            self._cset_path = self._absolute_path_for_command("cset", ["--help"])

        return self._cset_path is not None and self._cset_path is not False

    def get_cset(self):
        return self._cset_path

    def set_cset(self, cset_path):
        self._cset_path = cset_path

    def ensure_denoise(self):
        if self._denoise_path is None:
            if os.access(denoise_py, os.X_OK):
                self._denoise_path = denoise_py
            elif not os.path.isfile(denoise_py):
                raise UIError(
                    f"{denoise_py} not found. "
                    "Could it be that the user has no access to the file? "
                    "To use ReBench without denoise, use the --no-denoise option.\n",
                    None,
                )
            else:
                raise UIError(
                    f"{denoise_py} not marked executable. "
                    f"Please run something similar to `chmod a+x {denoise_py}`. "
                    "To use ReBench without denoise, use the --no-denoise option.\n",
                    None,
                )

        return self._denoise_path is not None and self._denoise_path is not False

    def get_denoise(self):
        self.ensure_denoise()
        return self._denoise_path


paths = CommandsPaths()


def _can_set_niceness() -> Union[bool, str]:
    """
    Check whether we can ask the operating system to influence the priority of
    our benchmarks.
    """
    try:
        out = check_output(["nice", "-n-20", "echo", "test"], stderr=STDOUT)
        output = output_as_str(out)
    except OSError:
        return "failed: OSError"

    if output is not None and (
        "cannot set niceness" in output or "Permission denied" in output
    ):
        return "failed: permission denied"
    else:
        return True


def _shield_lower_bound(num_cores):
    return int(floor(log(num_cores)))


def _shield_upper_bound(num_cores):
    return num_cores - 1


def _get_core_spec(num_cores) -> str:
    min_cores = _shield_lower_bound(num_cores)
    max_cores = _shield_upper_bound(num_cores)
    core_spec = "%d-%d" % (min_cores, max_cores)
    return core_spec


# pylint: disable-next=too-many-return-statements
def _activate_shielding(shield, num_cores) -> str:
    if not num_cores:
        return "failed: num-cores not set"

    if shield == "basic":
        core_spec = _get_core_spec(num_cores)
    else:
        core_spec = shield

    if not paths.has_cset():
        return "failed: cset-path not set"

    try:
        out = check_output(
            [paths.get_cset(), "shield", "-c", core_spec, "-k", "on"], stderr=STDOUT
        )
        output = output_as_str(out)
    except OSError as e:
        return "failed: " + str(e)

    if output is None:
        return "failed: no output"

    if "Permission denied" in output:
        return "failed: Permission denied"

    if "kthread shield activated" in output:
        return core_spec

    return "failed: " + output


def _reset_shielding() -> Union[str, bool]:
    if not paths.has_cset():
        return "failed: cset-path not set"

    try:
        out = check_output([paths.get_cset(), "shield", "-r"], stderr=STDOUT)
        output = output_as_str(out)
        return output is not None and "cset: done" in output
    except OSError:
        return "failed: OSError"
    except CalledProcessError:
        return "failed: CalledProcessError"


DEFAULT_SHIELD = "basic"

# For intel_pstate systems, there's only powersave and performance
SCALING_GOVERNOR_POWERSAVE = "powersave"
SCALING_GOVERNOR_PERFORMANCE = "performance"
DEFAULT_SCALING_GOVERNOR = SCALING_GOVERNOR_PERFORMANCE


def _read_scaling_governor() -> Optional[str]:
    try:
        with open(
            "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor",
            "r",
            encoding="utf-8",
        ) as gov_file:
            return gov_file.read().strip()
    except IOError:
        return None


def _set_scaling_governor(governor, num_cores) -> str:
    if governor not in (SCALING_GOVERNOR_POWERSAVE, SCALING_GOVERNOR_PERFORMANCE):
        print(
            "The scaling governor is expected to be 'performance' or 'powersave', but was "
            + governor
        )
        sys.exit(EXIT_CODE_INVALID_SETTINGS)

    if not num_cores:
        return "failed: num-cores not set"

    try:
        for cpu_i in range(num_cores):
            filename = f"/sys/devices/system/cpu/cpu{cpu_i}/cpufreq/scaling_governor"
            with open(filename, "w", encoding="utf-8") as gov_file:
                gov_file.write(governor + "\n")
    except IOError:
        return "failed: IOError"

    return governor


def _read_no_turbo() -> Optional[bool]:
    try:
        with open(
            "/sys/devices/system/cpu/intel_pstate/no_turbo", "r", encoding="utf-8"
        ) as nt_file:
            return nt_file.read().strip() == "1"
    except IOError:
        return None


def _set_no_turbo(with_no_turbo: bool) -> Union[Literal[True], str]:
    if with_no_turbo:
        value = "1"
    else:
        value = "0"

    try:
        with open(
            "/sys/devices/system/cpu/intel_pstate/no_turbo", "w", encoding="utf-8"
        ) as nt_file:
            nt_file.write(value + "\n")
    except IOError:
        return "failed: IOError"

    return True


def _configure_perf_sampling(for_profiling: bool) -> Union[Literal[True], str]:
    try:
        with open(
            "/proc/sys/kernel/perf_cpu_time_max_percent", "w", encoding="utf-8"
        ) as perc_file:
            if for_profiling:
                perc_file.write("0\n")
            else:
                perc_file.write("1\n")

        with open(
            "/proc/sys/kernel/perf_event_max_sample_rate", "w", encoding="utf-8"
        ) as sample_file:
            # for profiling we just disabled it above, and then don't need to set it
            if not for_profiling:
                sample_file.write("1\n")

        if for_profiling:
            with open(
                "/proc/sys/kernel/perf_event_paranoid", "w", encoding="utf-8"
            ) as perf_file:
                perf_file.write("-1\n")
    except IOError:
        return "failed: IOError"

    return True


def _restore_perf_sampling() -> str:
    try:
        with open(
            "/proc/sys/kernel/perf_cpu_time_max_percent", "w", encoding="utf-8"
        ) as perc_file:
            perc_file.write("25\n")

        with open(
            "/proc/sys/kernel/perf_event_max_sample_rate", "w", encoding="utf-8"
        ) as sample_file:
            sample_file.write("50000\n")

        with open(
            "/proc/sys/kernel/perf_event_paranoid", "w", encoding="utf-8"
        ) as perf_file:
            perf_file.write("3\n")
    except IOError:
        return "failed: IOError"
    return "restored"


def _initial_settings_and_capabilities(
    args,
) -> Mapping[str, Union[str, bool, None]]:
    result = {}

    if args.use_nice:
        r = _can_set_niceness()
        result["can_set_nice"] = r is True

    if args.use_shielding:
        num_cores = int(args.num_cores) if args.num_cores else None
        if paths.has_cset() and num_cores:
            shield = args.shield or DEFAULT_SHIELD
            output = _activate_shielding(shield, num_cores)
            if "failed" not in output:
                _reset_shielding()
                can_use_shielding = True
            else:
                can_use_shielding = False
        else:
            can_use_shielding = False
        result["can_set_shield"] = can_use_shielding

    if args.use_no_turbo:
        initial_no_turbo = _read_no_turbo()
        can_set_no_turbo = False

        if initial_no_turbo is not None and not initial_no_turbo:
            r = _set_no_turbo(True)
            can_set_no_turbo = r is True
            if can_set_no_turbo:
                _set_no_turbo(False)

        result["can_set_no_turbo"] = can_set_no_turbo
        result["initial_no_turbo"] = initial_no_turbo  # type: ignore

    if args.use_scaling_governor:
        initial_governor = _read_scaling_governor()
        can_set_governor = False

        if (
            initial_governor is not None
            and initial_governor != SCALING_GOVERNOR_PERFORMANCE
        ):
            r = _set_scaling_governor(SCALING_GOVERNOR_PERFORMANCE, num_cores)
            can_set_governor = r == SCALING_GOVERNOR_PERFORMANCE

        result["can_set_scaling_governor"] = can_set_governor
        result["initial_scaling_governor"] = initial_governor  # type: ignore

    if args.use_mini_perf_sampling:
        can_minimize_perf_sampling = (
            _configure_perf_sampling(args.for_profiling) != "failed"
        )
        if can_minimize_perf_sampling:
            _restore_perf_sampling()
        result["can_minimize_perf_sampling"] = can_minimize_perf_sampling

    return result


def _minimize_noise(args) -> dict:
    num_cores = int(args.num_cores) if args.num_cores else None
    result = {}

    if args.use_shielding:
        shield = args.shield or DEFAULT_SHIELD
        result["shielding"] = _activate_shielding(shield, num_cores)

    if args.use_no_turbo:
        r = _set_no_turbo(True)
        result["no_turbo"] = "succeeded" if r is True else r

    if args.use_scaling_governor:
        scaling_governor = args.scaling_governor or DEFAULT_SCALING_GOVERNOR
        result["scaling_governor"] = _set_scaling_governor(scaling_governor, num_cores)

    if args.use_mini_perf_sampling:
        r = _configure_perf_sampling(args.for_profiling)
        result["perf_event_max_sample_rate"] = "succeeded" if r is True else r

    return result


def _restore_standard_settings(args):
    num_cores = int(args.num_cores) if args.num_cores else None
    result = {}

    if args.use_shielding:
        result["shielding"] = _reset_shielding()

    if args.use_no_turbo:
        result["no_turbo"] = _set_no_turbo(False)

    if args.use_scaling_governor:
        result["scaling_governor"] = _set_scaling_governor(
            SCALING_GOVERNOR_POWERSAVE, num_cores
        )

    if args.use_mini_perf_sampling:
        result["perf_event_max_sample_rate"] = _restore_perf_sampling()

    return result


# pylint: disable-next=inconsistent-return-statements
def _exec(args, remaining_args) -> str:
    num_cores = int(args.num_cores) if args.num_cores else None

    cmdline = []
    if args.use_shielding:
        if not paths.has_cset():
            return "cset-path not set"
        if not num_cores:
            return "num-cores not set"

        cmdline += [paths.get_cset(), "shield", "--exec", "--"]

    if args.use_nice:
        cmdline += ["nice", "-n-20"]
    cmdline += remaining_args

    # the first element of cmdline is ignored as argument, since it's the file argument, too
    cmd = cmdline[0]

    # communicate the used core spec to executed command as part of its environment
    env = os.environ.copy()
    if args.use_shielding:
        assert paths.has_cset()
        assert num_cores
        core_spec = _get_core_spec(num_cores)
        env["REBENCH_DENOISE_CORE_SET"] = core_spec

    os.execvpe(cmd, cmdline, env)


def _kill(proc_id):
    return kill_process(int(proc_id), True, None, None)


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
    env_spec = os.environ.get("REBENCH_DENOISE_CORE_SET", None)
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
    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output results as JSON for processing",
    )
    parser.add_argument(
        "-N",
        "--without-nice",
        action="store_false",
        default=True,
        dest="use_nice",
        help="Don't try setting process niceness",
    )
    parser.add_argument(
        "-S",
        "--without-shielding",
        action="store_false",
        default=True,
        dest="use_shielding",
        help="Don't try shielding cores",
    )
    parser.add_argument(
        "-s",
        "--shield",
        action="store",
        default=None,
        dest="shield",
        help=f"Shielding specification. Default is '{DEFAULT_SHIELD}'.",
    )
    parser.add_argument(
        "-T",
        "--without-no-turbo",
        action="store_false",
        default=True,
        dest="use_no_turbo",
        help="Don't try setting no_turbo",
    )
    parser.add_argument(
        "-G",
        "--without-scaling-governor",
        action="store_false",
        default=True,
        dest="use_scaling_governor",
        help="Don't try setting scaling governor",
    )
    parser.add_argument(
        "-g",
        "--governor",
        action="store",
        default=None,
        dest="scaling_governor",
        help=f"Scaling Governor to set. Default value is '{DEFAULT_SCALING_GOVERNOR}'.",
    )
    parser.add_argument(
        "-P",
        "--without-min-perf-sampling",
        action="store_false",
        default=True,
        dest="use_mini_perf_sampling",
        help="Don't try to minimize perf sampling",
    )
    parser.add_argument(
        "-p",
        "--for-profiling",
        action="store_true",
        default=False,
        dest="for_profiling",
        help="Don't restrict CPU usage by profiler",
    )
    parser.add_argument(
        "--cset-path",
        help="Absolute path to cset. Needed for `init`, `minimize`, and `restore`.",
        default=None,
    )
    parser.add_argument(
        "--num-cores",
        help="Number of cores. Needed for `init`, `minimize`, and `restore`.",
        default=None,
    )
    parser.add_argument(
        "command",
        help=(
            "`init`|`minimize`|`restore`|`exec -- `|`kill pid`|`test`: "
            "`init` determines initial settings and capabilities. "
            "`minimize` sets system to reduce noise. "
            "`restore` sets system to the assumed original settings. "
            "`exec -- ` executes the given command with arguments. "
            "`kill pid` send kill signal to the process with given id "
            "and all child processes. "
            "`test` executes a computation for 20 seconds in parallel. "
            "It is only useful to test rebench-denoise itself."
        ),
        default=None,
    )
    return parser


EXIT_CODE_SUCCESS = 0
EXIT_CODE_CHANGING_SETTINGS_FAILED = 1
EXIT_CODE_NUM_CORES_UNSET = 2
EXIT_CODE_NO_COMMAND_SELECTED = 3
EXIT_CODE_EXEC_FAILED = 4
EXIT_CODE_INVALID_SETTINGS = 5


def _report_init(result: dict, args):
    if args.use_nice:
        print("Can set niceness: ", result.get("can_set_nice", "Unknown"))

    if args.use_shielding:
        print("Can use shielding: ", result.get("can_set_shield", "Unknown"))

    if args.use_no_turbo:
        print("Can set no_turbo: ", result.get("can_set_no_turbo", "Unknown"))
        print("Initial no_turbo: ", result.get("initial_no_turbo", "Unknown"))

    if args.use_scaling_governor:
        print(
            "Can set scaling_governor: ",
            result.get("can_set_scaling_governor", "Unknown"),
        )
        print(
            "Initial scaling_governor: ",
            result.get("initial_scaling_governor", "Unknown"),
        )

    if args.use_mini_perf_sampling:
        print(
            "Can minimize perf sampling: ",
            result.get("can_minimize_perf_sampling", "Unknown"),
        )


def _report(result: Union[str, dict], args):
    if isinstance(result, str):
        print(result)
        return

    if args.use_nice and args.command == "exec":
        print("Can set niceness:                   ", result.get("can_set_nice", False))

    if args.use_shielding:
        print("Enabled core shielding:             ", result.get("shielding", False))

    if args.use_scaling_governor:
        print(
            "Setting scaling_governor:           ", result.get("scaling_governor", None)
        )

    if args.use_no_turbo:
        print("Setting no_turbo:                   ", result.get("no_turbo", False))

    if args.use_mini_perf_sampling:
        print(
            "Setting perf_event_max_sample_rate: ",
            result.get("perf_event_max_sample_rate", None),
        )


def _any_failed(result: dict):
    return any(str(v).startswith("failed") for v in result.values())


def _check_for_inconsistent_settings(args):
    if args.use_shielding is False and args.shield is not None:
        print(
            "Error: -s|--shield can only be set "
            "when -S|--without-shielding is not set."
        )
        sys.exit(EXIT_CODE_INVALID_SETTINGS)

    if args.use_scaling_governor is False and args.scaling_governor is not None:
        print(
            "Error: -g|--governor can only be set "
            "when -G|--without-scaling-governor is not set."
        )
        sys.exit(EXIT_CODE_INVALID_SETTINGS)


def main_func():
    arg_parser = _shell_options()
    args, remaining_args = arg_parser.parse_known_args()

    paths.set_cset(args.cset_path)

    _check_for_inconsistent_settings(args)

    result = {}

    if args.command == "init":
        result = _initial_settings_and_capabilities(args)
    elif args.command == "minimize":
        result = _minimize_noise(args)
    elif args.command == "restore":
        result = _restore_standard_settings(args)
    elif args.command == "exec":
        result = _exec(args, remaining_args)
    elif args.command == "kill":
        _kill(remaining_args[0])
    elif args.command == "test":
        _test(args)
    else:
        arg_parser.print_help()
        return EXIT_CODE_NO_COMMAND_SELECTED

    if args.json:
        print(json.dumps(result))
    else:
        if args.command == "init":
            _report_init(result, args)
        if args.command == "exec":
            # should not have returned
            print(result)
            return EXIT_CODE_EXEC_FAILED
        else:
            _report(result, args)

    if _any_failed(result):
        return EXIT_CODE_CHANGING_SETTINGS_FAILED
    else:
        return EXIT_CODE_SUCCESS


if __name__ == "__main__":
    sys.exit(main_func())
