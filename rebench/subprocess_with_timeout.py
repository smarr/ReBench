from os         import kill
from signal     import SIGKILL
from subprocess import PIPE, Popen
from threading  import Thread


class SubprocessThread(Thread):

    def __init__(self, binary_name, args, shell, cwd, stdout, stderr):
        Thread.__init__(self, name = "Subprocess %s" % binary_name)
        self._args   = args
        self._shell  = shell
        self._cwd    = cwd
        self._stdout = stdout
        self._stderr = stderr

        self.stdout_result = None
        self.stderr_result = None
        self.returncode    = None
        self.pid           = None

    def run(self):
        p = Popen(self._args, shell=self._shell, cwd=self._cwd,
                  stdout=self._stdout, stderr=self._stderr)
        self.pid = p.pid

        self.stdout_result, self.stderr_result = p.communicate()
        self.returncode = p.returncode


def run(args, cwd = None, shell = False, kill_tree = True, timeout = -1,
        stdout = PIPE, stderr = PIPE):
    """
    Run a command with a timeout after which it will be forcibly
    killed.
    """
    binary_name = args.split(' ')[0]

    thread = SubprocessThread(binary_name, args, shell, cwd, stdout, stderr)
    thread.start()

    if timeout == -1:
        thread.join()
    else:
        thread.join(timeout)

    if timeout != -1 and thread.is_alive():
        assert thread.pid is not None
        return kill_process(thread.pid, kill_tree)

    return thread.returncode, thread.stdout_result, thread.stderr_result


def kill_process(pid, recursively):
    pids = [pid]
    if recursively:
        pids.extend(get_process_children(pid))

    for p in pids:
        kill(p, SIGKILL)

    return -9, '', ''


def get_process_children(pid):
    p = Popen('ps --no-headers -o pid --ppid %d' % pid, shell = True,
              stdout = PIPE, stderr = PIPE)
    stdout, _stderr = p.communicate()
    result = [int(p) for p in stdout.split()]
    for child in result[:]:
        result.extend(get_process_children(child))
    return result

