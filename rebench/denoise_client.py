import getpass
import json
import os
import subprocess

from cpuinfo import get_cpu_info

from .denoise import paths
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
    return add_denoise_python_path_to_env(os.environ)


def add_denoise_python_path_to_env(env):
    path = paths.get_denoise_python_path()

    # did not find it, just leave the env unmodified
    if path is False:
        return env

    env = env.copy()
    if 'PYTHONPATH' in env and env['PYTHONPATH']:
        env['PYTHONPATH'] += os.pathsep + path
    else:
        env['PYTHONPATH'] = path
    return env


class DenoiseResult:

    def __init__(self, succeeded, warn_msg, use_nice, use_shielding, details):
        self.succeeded = succeeded
        self.warn_msg = warn_msg
        self.use_nice = use_nice
        self.use_shielding = use_shielding
        self.details = details


def minimize_noise(show_warnings, ui, for_profiling):  # pylint: disable=too-many-statements
    num_cores = get_number_of_cores()

    result = {}

    env = _get_env_with_python_path_for_denoise()
    cmd = ['sudo', '--preserve-env=PYTHONPATH', '-n', paths.get_denoise()]
    if for_profiling:
        cmd += ['--for-profiling']

    if paths.has_cset():
        cmd += ['--cset-path', paths.get_cset()]
    cmd += ['--json', 'minimize']
    cmd += ['--num-cores', str(num_cores)]

    try:
        output = output_as_str(subprocess.check_output(cmd,
                                                       stderr=subprocess.STDOUT,
                                                       env=env))
        try:
            result = json.loads(output)
            got_json = True
        except ValueError:
            got_json = False
    except subprocess.CalledProcessError as e:
        output = output_as_str(e.output)
        got_json = False
    except FileNotFoundError as e:
        output = str(e)
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
            msg += '{ind}Please make sure `sudo ' + paths.get_denoise() + '`' \
                   + ' can be used without password.\n'
            msg += '{ind}To be able to run rebench-denoise without password,\n'
            msg += '{ind}add the following to the end of your sudoers file (using visudo):\n'
            msg += '{ind}{ind}' + getpass.getuser() + ' ALL = (root) NOPASSWD:SETENV: '\
                   + paths.get_denoise() + '\n'
        elif 'command not found' in output:
            msg += '{ind}Please make sure `rebench-denoise` is on the PATH\n'
        elif "No such file or directory: 'sudo'" in output:
            msg += '{ind}sudo is not available. Can\'t use rebench-denoise to manage the system.\n'
        else:
            msg += '{ind}Error: ' + escape_braces(output)

    if not success and show_warnings:
        ui.warning(msg)

    return DenoiseResult(success, msg, use_nice, use_shielding, result)


def restore_noise(denoise_result, show_warning, ui):
    if not denoise_result:
        # likely has failed completely. And without details, just no-op
        return

    num_cores = get_number_of_cores()

    env = _get_env_with_python_path_for_denoise()
    values = set(denoise_result.details.values())
    if len(values) == 1 and "failed" in values:
        # everything failed, don't need to try to restore things
        pass
    else:
        try:
            cmd = ['sudo', '--preserve-env=PYTHONPATH', '-n', paths.get_denoise(), '--json']
            if not denoise_result.use_shielding:
                cmd += ['--without-shielding']
            if not denoise_result.use_nice:
                cmd += ['--without-nice']
            cmd += ['--num-cores', str(num_cores)]
            subprocess.check_output(cmd + ['restore'], stderr=subprocess.STDOUT, env=env)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass

    if not denoise_result.succeeded and show_warning:
        # warn a second time at the end of the execution
        ui.error(denoise_result.warn_msg)


def deliver_kill_signal(pid):
    env = _get_env_with_python_path_for_denoise()

    try:
        cmd = ['sudo', '--preserve-env=PYTHONPATH',
               '-n', paths.get_denoise(), '--json', 'kill', str(pid)]
        subprocess.check_output(cmd, stderr=subprocess.STDOUT, env=env)
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
