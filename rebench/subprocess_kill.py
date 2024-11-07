from os         import kill
from signal     import SIGKILL
from subprocess import PIPE, Popen
from typing     import Optional, Tuple

# Indicate timeout with standard exit code
E_TIMEOUT = -9


def _kill(proc_id, sudo_kill_delivery_fn):
    if sudo_kill_delivery_fn:
        sudo_kill_delivery_fn(proc_id)
        return

    try:
        kill(proc_id, SIGKILL)
    except ProcessLookupError:  # pylint: disable=undefined-variable
        # there's a race condition, the process may have already terminated on its own
        # so let's simply ignore it
        pass


def kill_process(pid, recursively, thread, sudo_kill_delivery_fn
                 ) -> Tuple[int, Optional[str], Optional[str]]:
    pids = [pid]
    if recursively:
        pids.extend(_get_process_children(pid))

    for proc_id in pids:
        _kill(proc_id, sudo_kill_delivery_fn)

    if thread:
        thread.join()
        return E_TIMEOUT, thread.stdout_result, thread.stderr_result
    return E_TIMEOUT, None, None


def _get_process_children(pid):
    # pylint: disable-next=consider-using-with
    proc = Popen("pgrep -P %d" % pid, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, _stderr = proc.communicate()
    result = [int(p) for p in stdout.split()]
    for child in result[:]:
        result.extend(_get_process_children(child))
    return result
