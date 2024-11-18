import getpass
import json
import os

from subprocess import check_output, STDOUT, CalledProcessError
from typing import Optional, Tuple
from cpuinfo import get_cpu_info

from .denoise import paths, DEFAULT_SCALING_GOVERNOR
from .model.denoise import Denoise
from .output import output_as_str
from .ui import escape_braces


_num_cpu_cores = None


def get_number_of_cores():
    global _num_cpu_cores  # pylint: disable=global-statement
    if _num_cpu_cores is None:
        cpu_info = get_cpu_info()
        _num_cpu_cores = cpu_info["count"]
    return _num_cpu_cores


def _get_env_with_python_path_for_denoise():
    return _add_denoise_python_path_to_env(os.environ)


def _add_denoise_python_path_to_env(env: dict[str, str]) -> dict[str, str]:
    path = paths.get_denoise_python_path()

    # did not find it, just leave the env unmodified
    if path is False:
        print("Could not find the Python path for rebench-denoise.")
        return env

    env = env.copy()
    if "PYTHONPATH" in env and env["PYTHONPATH"]:
        env["PYTHONPATH"] += os.pathsep + path
    else:
        env["PYTHONPATH"] = path
    return env


class DenoiseInitialSettings:
    """
    This class is used to store the initial system settings that are changed by rebench-denoise.
    """

    def __init__(self, requested: Denoise, result: dict, warn_msg: Optional[str]):
        self.requested = requested

        can_set = [v for k, v in result.items() if k.startswith("can_")]
        self.nothing_set = not any(can_set)

        self.can_set_nice = result.get("can_set_nice", None)
        self.can_set_shield = result.get("can_set_shield", None)
        self.can_set_no_turbo = result.get("can_set_no_turbo", None)
        self.can_set_scaling_governor = result.get("can_set_scaling_governor", None)
        self.can_minimize_perf_sampling = result.get("can_minimize_perf_sampling", None)

        self.initial_no_turbo = result.get("initial_no_turbo", None)
        self.initial_scaling_governor = result.get("initial_scaling_governor", None)

        self.warn_msg = warn_msg

        self._restore_init: Optional[Denoise] = None

    def as_dict(self):
        return {
            "can_set_nice": self.can_set_nice,
            "can_set_shield": self.can_set_shield,
            "can_set_no_turbo": self.can_set_no_turbo,
            "can_set_scaling_governor": self.can_set_scaling_governor,
            "can_minimize_perf_sampling": self.can_minimize_perf_sampling,

            "initial_no_turbo": self.initial_no_turbo,
            "initial_scaling_governor": self.initial_scaling_governor
        }

    def restore_initial(self) -> Denoise:
        if self._restore_init is None:
            self._restore_init = self.requested.restore_initial(self)
        return self._restore_init

    @staticmethod
    def system_default() -> "DenoiseInitialSettings":
        return DenoiseInitialSettings(Denoise.system_default(), {}, None)


def _construct_basic_path(env_keys: list[str]) -> list[str]:
    assert len(env_keys) > 0
    return ["sudo", "--preserve-env=" + ",".join(env_keys), "-n", paths.get_denoise(), "--json"]


def _construct_path(for_profiling: bool, env_keys: list[str]) -> list[str]:
    num_cores = get_number_of_cores()
    cmd = _construct_basic_path(env_keys)
    cmd += ["--num-cores", str(num_cores)]

    if paths.has_cset():
        cmd += ["--cset-path", paths.get_cset()]

    if for_profiling:
        cmd += ["--for-profiling"]

    return cmd


def _add_denoise_options(cmd: list[str], requested: Denoise):
    """This function is used for initializing and minimizing noise."""
    assert requested.needs_denoise()

    options_to_disable = ""

    if not requested.requested_nice:
        options_to_disable += "N"
    if not requested.requested_shield:
        options_to_disable += "S"
    if not requested.requested_scaling_governor:
        options_to_disable += "G"
    elif requested.scaling_governor != DEFAULT_SCALING_GOVERNOR:
        cmd.append("-g")
        cmd.append(requested.scaling_governor)
    if not requested.requested_no_turbo:
        options_to_disable += "T"
    if not requested.requested_minimize_perf_sampling:
        options_to_disable += "P"

    if options_to_disable:
        cmd.append("-" + options_to_disable)


def _add_denoise_exec_options(cmd: list[str], requested: Denoise):
    """This function is used for executing a command."""
    options_to_disable = ""

    if not requested.requested_nice:
        options_to_disable += "N"
    if not requested.requested_shield:
        options_to_disable += "S"

    if options_to_disable:
        cmd.append("-" + options_to_disable)


def _exec_denoise(cmd: list[str]):
    env = _get_env_with_python_path_for_denoise()
    try:
        output = output_as_str(check_output(cmd, stderr=STDOUT, env=env))
    except CalledProcessError as e:
        output = output_as_str(e.output)
    except FileNotFoundError as e:
        output = str(e)
    return output


def _exec_denoise_and_parse_result(cmd: list[str]) -> Tuple[dict, bool, str]:
    output = _exec_denoise(cmd)

    try:
        result = json.loads(output)
        got_json = True
    except ValueError:
        result = {}
        got_json = False

    return result, got_json, output


def get_initial_settings_and_capabilities(
        show_warnings, ui, requested: Denoise) -> Optional[DenoiseInitialSettings]:
    if not requested.needs_denoise():
        return None

    cmd = _construct_path(False, ["PYTHONPATH"])
    _add_denoise_options(cmd, requested)
    cmd += ["init"]

    result, got_json, raw_output = _exec_denoise_and_parse_result(cmd)

    success = False

    if got_json:
        msg = ""
        success = True
        for k, value in result.items():
            if k.startswith("can_") and value is False:
                if success:
                    msg = "Minimizing noise with rebench-denoise was not complete.\n" \
                          "{ind}This may cause benchmark results to vary more.\n\n"

                success = False
                if k == "can_set_nice":
                    msg += "{ind}Process niceness could not be set.\n"
                elif k == "can_set_shield":
                    msg += "{ind}Core shielding could not be set up.\n"
                    if not paths.has_cset():
                        msg += ("{ind}{ind}cset is part of the cpuset package on Debian, Ubuntu,"
                                " and OpenSuSE. The code is maintained here:"
                                " https://github.com/SUSE/cpuset\n")
                elif k == "can_set_no_turbo":
                    msg += "{ind}Turbo mode could not be disabled.\n"
                elif k == "can_set_scaling_governor":
                    msg += "{ind}Scaling governor could not be set.\n"
                elif k == "can_minimize_perf_sampling":
                    msg += "{ind}Perf sampling frequency could not be minimized.\n"
                else:
                    msg += "{ind}Unknown capability: " + k + "\n"
    else:
        msg = _report_on_failure(raw_output)

    if not success and show_warnings:
        ui.warning(msg)

    return DenoiseInitialSettings(requested, result, msg)


def _report_on_failure(output):
    if 'password is required' in output:
        return '{ind}Please make sure `sudo ' + paths.get_denoise() + '`' \
               ' can be used without password.\n' \
               '{ind}To be able to run rebench-denoise without password,\n' \
               '{ind}add the following to the end of your sudoers file (using visudo):\n' \
               '{ind}{ind}' + getpass.getuser() + ' ALL = (root) NOPASSWD:SETENV: ' \
               + paths.get_denoise() + '\n'
    elif 'command not found' in output:
        return '{ind}Please make sure `rebench-denoise` is on the PATH\n'
    elif "No such file or directory: 'sudo'" in output:
        return "{ind}sudo is not available. Can't use rebench-denoise to manage the system.\n"
    else:
        return "{ind}Error: " + escape_braces(output)


def _process_denoise_result(
        result, got_json, raw_output, msg, show_warnings, ui, possible_settings):
    success = True

    if got_json:
        failed = ""

        for k, value in result.items():
            if isinstance(value, str) and value.startswith("failed"):
                failed += "{ind}{ind} - " + k + " " + value + "\n"
                success = False

        if not success:
            msg += "{ind}Failed to set:\n" + failed + "\n"
    else:
        msg += _report_on_failure(raw_output)

    if not success and show_warnings:
        ui.warning(msg)

    if success:
        return possible_settings
    else:
        return None


def minimize_noise(possible_settings: Denoise, for_profiling: bool, show_warnings: bool, ui):
    if not possible_settings.needs_denoise():
        return possible_settings

    cmd = _construct_path(for_profiling, ["PYTHONPATH"])
    _add_denoise_options(cmd, possible_settings)
    cmd += ["minimize"]

    result, got_json, raw_output = _exec_denoise_and_parse_result(cmd)

    msg = "Minimizing noise with rebench-denoise failed\n"
    msg += "{ind}possibly causing benchmark results to vary more.\n\n"
    return _process_denoise_result(
        result, got_json, raw_output, msg, show_warnings, ui, possible_settings)


def construct_denoise_exec_prefix(
        env, for_profiling, possible_settings: Denoise) -> Tuple[str, dict]:
    env = _add_denoise_python_path_to_env(env)
    cmd = _construct_path(for_profiling, env.keys())

    _add_denoise_exec_options(cmd, possible_settings)

    cmd += ["exec", "--"]
    return " ".join(cmd) + " ", env

def restore_noise(denoise_result: DenoiseInitialSettings, show_warning, ui):
    if denoise_result.nothing_set:
        # if nothing was set, then nothing to restore

        if show_warning and denoise_result.warn_msg:
            # warn a second time at the end of the execution
            ui.error(denoise_result.warn_msg)
        return Denoise.system_default()

    restore = denoise_result.restore_initial()
    if not restore.needs_denoise():
        # nothing to restore

        if show_warning and denoise_result.warn_msg:
            # warn a second time at the end of the execution
            ui.error(denoise_result.warn_msg)
        return Denoise.system_default()

    cmd = _construct_path(False, ["PYTHONPATH"])
    _add_denoise_options(cmd, restore)
    cmd += ["restore"]

    result, got_json, raw_output = _exec_denoise_and_parse_result(cmd)

    restored = _process_denoise_result(
        result, got_json, raw_output,
        "Restoring system defaults with rebench-denoise failed.\n", False, ui,
        Denoise.system_default())

    if show_warning and denoise_result.warn_msg:
        # warn a second time at the end of the execution
        ui.error(denoise_result.warn_msg)

    return restored


def deliver_kill_signal(pid):
    cmd = _construct_basic_path(["PYTHONPATH"])
    cmd += ["kill", str(pid)]
    _exec_denoise(cmd)
