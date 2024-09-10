import getpass
import json
import os
import subprocess

from cpuinfo import get_cpu_info

from .denoise import paths, read_no_turbo, read_scaling_governor
from .output import output_as_str
from .ui import escape_braces


_num_cpu_cores = None


def get_number_of_cores():
    global _num_cpu_cores  # pylint: disable=global-statement
    if _num_cpu_cores is None:
        cpu_info = get_cpu_info()
        _num_cpu_cores = cpu_info["count"]
    return _num_cpu_cores


class DenoiseResult:

    def __init__(self, succeeded, warn_msg, use_nice, use_shielding, details):
        self.succeeded = succeeded
        self.warn_msg = warn_msg
        self.use_nice = use_nice
        self.use_shielding = use_shielding
        self.details = details


class DenoiseInitialSettings:
    def __init__(self, requested):
        self.requested = requested

        self.can_set_nice = can_set_nice
        self.can_set_shield = can_set_shield
        self.can_minimize_perf_sampling = can_minimize_perf_sampling

        self.default_scaling_governor = default_scaling_governor
        self.default_no_turbo = default_no_turbo

def get_initial_settings_and_capabilities(requested):
    if requested.use_nice:

    check_capabilities(requested.use_nice, requested.shield)

    no_turbo = read_no_turbo()
    scaling_governor = read_scaling_governor()
    return DenoiseInitialSettings(no_turbo, scaling_governor)


def minimize_noise(show_warnings, ui, for_profiling):  # pylint: disable=too-many-statements
    num_cores = get_number_of_cores()

    result = {}

    env = os.environ
    cmd = ["sudo", "-n", paths.get_denoise()]
    if for_profiling:
        cmd += ["--for-profiling"]

    if paths.has_cset():
        cmd += ["--cset-path", paths.get_cset()]
    cmd += ["--json", "minimize"]
    cmd += ["--num-cores", str(num_cores)]

    try:
        output = output_as_str(
            subprocess.check_output(cmd, stderr=subprocess.STDOUT, env=env))
    except subprocess.CalledProcessError as e:
        output = output_as_str(e.output)
    except FileNotFoundError as e:
        print("FileNotFoundError")
        output = str(e)

    try:
        result = json.loads(output)
        got_json = True
    except ValueError:
        got_json = False

    msg = "Minimizing noise with rebench-denoise failed\n"
    msg += "{ind}possibly causing benchmark results to vary more.\n\n"

    success = False
    use_nice = False
    use_shielding = False

    if got_json:
        use_nice = result.get("can_set_nice", False)
        use_shielding = result.get("shielding", False)

        failed = ""

        for k, value in result.items():
            if value == "failed":
                failed += "{ind}{ind} - " + k + "\n"

        if not use_nice:
            failed += "{ind}{ind} - nice was not used\n"
        if not use_shielding:
            failed += "{ind}{ind} - core shielding was not used\n"

        if failed:
            msg += "{ind}Failed to set:\n" + failed + "\n"

        if not use_nice and show_warnings:
            msg += ("{ind}Process niceness could not be set.\n"
                    + "{ind}{ind}`nice` is used to elevate the priority of the benchmark,\n"
                    + "{ind}{ind}without it, other processes my interfere with it"
                    + " nondeterministically.\n")

        if not use_shielding and show_warnings:
            msg += "{ind}Core shielding could not be set up"

            if not paths.has_cset():
                msg += ", because the cset command was not found.\n"
            else:
                msg += ".\n"

            msg += ("{ind}{ind}Shielding is used to restrict the use of cores to"
                    + " benchmarking.\n"
                    + "{ind}{ind}Without it, there my be more nondeterministic interference.\n")

            if not paths.has_cset():
                msg += ("{ind}{ind}cset is part of the cpuset package on Debian, Ubuntu," +
                        " and OpenSuSE. The code is maintained here:" +
                        " https://github.com/SUSE/cpuset\n")

        if use_nice and use_shielding and not failed:
            success = True
    else:
        if 'password is required' in output:
            msg += '{ind}Please make sure `sudo ' + paths.get_denoise() + '`' \
                   + ' can be used without password.\n'
            msg += '{ind}To be able to run denoise without password,\n'
            msg += '{ind}add the following to the end of your sudoers file (using visudo):\n'
            msg += '{ind}{ind}' + getpass.getuser() + ' ALL = (root) NOPASSWD:SETENV: '\
                   + paths.get_denoise() + '\n'
        elif 'command not found' in output:
            msg += '{ind}Please make sure ' + paths.get_denoise() + ' is accessible.\n'
        elif "No such file or directory: 'sudo'" in output:
            msg += "{ind}sudo is not available. Can't use denoise to manage the system.\n"
        else:
            msg += "{ind}Error: " + escape_braces(output)

    if not success and show_warnings:
        ui.warning(msg)

    return DenoiseResult(success, msg, use_nice, use_shielding, result)


def restore_noise(denoise_result, show_warning, ui):
    if not denoise_result:
        # likely has failed completely. And without details, just no-op
        return

    num_cores = get_number_of_cores()

    env = os.environ
    values = set(denoise_result.details.values())
    if len(values) == 1 and "failed" in values:
        # everything failed, don't need to try to restore things
        pass
    else:
        try:
            cmd = ["sudo", "-n", paths.get_denoise(), "--json"]
            if not denoise_result.use_shielding:
                cmd += ["--without-shielding"]
            elif paths.has_cset():
                cmd += ["--cset-path", paths.get_cset()]
            if not denoise_result.use_nice:
                cmd += ["--without-nice"]
            cmd += ["--num-cores", str(num_cores)]
            subprocess.check_output(cmd + ["restore"], stderr=subprocess.STDOUT, env=env)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    if not denoise_result.succeeded and show_warning:
        # warn a second time at the end of the execution
        ui.error(denoise_result.warn_msg)


def deliver_kill_signal(pid):
    env = os.environ

    try:
        cmd = ['sudo',
               '-n', paths.get_denoise(), '--json', 'kill', str(pid)]
        subprocess.check_output(cmd, stderr=subprocess.STDOUT, env=env)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
