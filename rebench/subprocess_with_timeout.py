from __future__ import print_function

from os         import kill
from select     import select
from signal     import SIGKILL
from subprocess import PIPE, STDOUT, Popen
from threading  import Thread, Condition
from time       import time

import sys

IS_PY3 = None

try:
    _ = ProcessLookupError
    IS_PY3 = True
except NameError:
    IS_PY3 = False

# Indicate timeout with standard exit code
E_TIMEOUT = -9


class _SubprocessThread(Thread):

    def __init__(self, executable_name, args, shell, cwd, verbose, stdout, stderr, stdin_input):
        Thread.__init__(self, name="Subprocess %s" % executable_name)
        self._args = args
        self._shell = shell
        self._cwd = cwd
        self._verbose = verbose
        self._stdout = stdout
        self._stderr = stderr
        self._stdin_input = stdin_input

        self._pid = None
        self._started_cv = Condition()

        self.stdout_result = None
        self.stderr_result = None
        self.returncode = None
        self._exception = None

    @property
    def exception(self):
        return self._exception

    def run(self):
        try:
            self._started_cv.acquire()
            stdin = PIPE if self._stdin_input else None
            proc = Popen(self._args, shell=self._shell, cwd=self._cwd,
                         stdin=stdin, stdout=self._stdout, stderr=self._stderr)
            self._pid = proc.pid
            self._started_cv.notify()
            self._started_cv.release()

            if self._stdin_input:
                proc.stdin.write(self._stdin_input)
                proc.stdin.flush()

            self.process_output(proc)
            self.returncode = proc.returncode
        except Exception as err:  # pylint: disable=broad-except
            self._exception = err

    def get_pid(self):
        self._started_cv.acquire()
        while self._pid is None:
            self._started_cv.wait()
        self._started_cv.release()
        return self._pid

    def process_output(self, proc):
        if self._verbose and self._stdout == PIPE and (self._stderr == PIPE or
                                                       self._stderr == STDOUT):
            self.stdout_result = ""
            self.stderr_result = ""

            while True:
                reads = [proc.stdout.fileno()]
                if self._stderr == PIPE:
                    reads.append(proc.stderr.fileno())
                ret = select(reads, [], [])

                for file_no in ret[0]:
                    if file_no == proc.stdout.fileno():
                        read = proc.stdout.readline()
                        sys.stdout.write(read)
                        self.stdout_result += read
                    if self._stderr == PIPE and file_no == proc.stderr.fileno():
                        read = proc.stderr.readline()
                        sys.stderr.write(read)
                        self.stderr_result += read

                if proc.poll() is not None:
                    break
        else:
            self.stdout_result, self.stderr_result = proc.communicate()


def _print_keep_alive(seconds_since_start):
    print("Keep alive, current job runs for %dmin\n" % (seconds_since_start / 60))


def run(args, cwd=None, shell=False, kill_tree=True, timeout=-1,
        verbose=False, stdout=PIPE, stderr=PIPE, stdin_input=None,
        keep_alive_output=_print_keep_alive):
    """
    Run a command with a timeout after which it will be forcibly
    killed.
    """
    executable_name = args.split(' ')[0]

    thread = _SubprocessThread(executable_name, args, shell, cwd, verbose, stdout,
                               stderr, stdin_input)
    thread.start()

    if timeout == -1:
        thread.join()
    else:
        t10min = 10 * 60
        if timeout < t10min:
            thread.join(timeout)
        else:
            start = time()
            diff = 0
            while diff < timeout:
                if t10min < timeout - diff:
                    max_10min_timeout = t10min
                else:
                    max_10min_timeout = timeout - diff
                thread.join(max_10min_timeout)
                if not thread.is_alive():
                    break
                diff = time() - start
                if diff < timeout:
                    keep_alive_output(diff)

    if timeout != -1 and thread.is_alive():
        assert thread.get_pid() is not None
        return _kill_process(thread.get_pid(), kill_tree, thread)

    if not thread.is_alive():
        exp = thread.exception
        if exp:
            raise exp  # pylint: disable=raising-bad-type

    return thread.returncode, thread.stdout_result, thread.stderr_result


def _kill_py2(proc_id):
    try:
        kill(proc_id, SIGKILL)
    except IOError:
        # it's a race condition, so let's simply ignore it
        pass


def _kill_py3(proc_id):
    try:
        kill(proc_id, SIGKILL)
    except ProcessLookupError:  # pylint: disable=undefined-variable
        # it's a race condition, so let's simply ignore it
        pass


def _kill_process(pid, recursively, thread):
    pids = [pid]
    if recursively:
        pids.extend(_get_process_children(pid))

    for proc_id in pids:
        if IS_PY3:
            _kill_py3(proc_id)
        else:
            _kill_py2(proc_id)

    thread.join()

    return E_TIMEOUT, thread.stdout_result, thread.stderr_result


def _get_process_children(pid):
    proc = Popen('pgrep -P %d' % pid, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, _stderr = proc.communicate()
    result = [int(p) for p in stdout.split()]
    for child in result[:]:
        result.extend(_get_process_children(child))
    return result
