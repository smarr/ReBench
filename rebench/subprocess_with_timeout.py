from select     import select
from subprocess import PIPE, STDOUT, Popen
from threading  import Thread, Condition
from time       import time

import sys
import signal

from .subprocess_kill import kill_process


# Indicate timeout with standard exit code
E_TIMEOUT = -9


def output_as_str(string_like):
    if string_like is not None and type(string_like) != str:  # pylint: disable=unidiomatic-typecheck
        return string_like.decode('utf-8')
    else:
        return string_like

_signals_setup = False


def keyboard_interrupt_on_sigterm(signum, frame):
    raise KeyboardInterrupt()


def _setup_signal_handling_if_needed():
    global _signals_setup  # pylint: disable=global-statement
    if not _signals_setup:
        _signals_setup = True
        signal.signal(signal.SIGTERM, keyboard_interrupt_on_sigterm)


class _SubprocessThread(Thread):

    def __init__(self, executable_name, args, env,
                 shell, cwd, verbose, stdout, stderr, stdin_input):
        Thread.__init__(self, name="Subprocess %s" % executable_name)
        self._args = args
        self._shell = shell
        self._cwd = cwd
        self._verbose = verbose
        self._stdout = stdout
        self._stderr = stderr
        self._stdin_input = stdin_input
        self._env = env

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

            # pylint: disable-next=consider-using-with
            proc = Popen(self._args, shell=self._shell, cwd=self._cwd,
                         stdin=stdin, stdout=self._stdout, stderr=self._stderr, env=self._env)
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
        if self._verbose and self._stdout == PIPE and self._stderr in (PIPE, STDOUT):
            self.stdout_result = ""
            self.stderr_result = ""

            while True:
                reads = [proc.stdout.fileno()]
                if self._stderr == PIPE:
                    reads.append(proc.stderr.fileno())
                ret = select(reads, [], [])

                for file_no in ret[0]:
                    if file_no == proc.stdout.fileno():
                        read = output_as_str(proc.stdout.readline())
                        sys.stdout.write(read)
                        self.stdout_result += read
                    if self._stderr == PIPE and file_no == proc.stderr.fileno():
                        read = output_as_str(proc.stderr.readline())
                        sys.stderr.write(read)
                        self.stderr_result += read

                if proc.poll() is not None:
                    break
        else:
            stdout_r, stderr_r = proc.communicate()
            self.stdout_result = output_as_str(stdout_r)
            self.stderr_result = output_as_str(stderr_r)


def _print_keep_alive(seconds_since_start):
    print("Keep alive, current job runs for %dmin\n" % (seconds_since_start / 60))


def run(args, env, cwd=None, shell=False, kill_tree=True, timeout=-1,
        verbose=False, stdout=PIPE, stderr=PIPE, stdin_input=None,
        keep_alive_output=_print_keep_alive, uses_sudo=False):
    """
    Run a command with a timeout after which it will be forcibly
    killed.
    """
    _setup_signal_handling_if_needed()
    executable_name = args.split(' ', 1)[0]

    thread = _SubprocessThread(executable_name, args, env, shell, cwd, verbose, stdout,
                               stderr, stdin_input)
    thread.start()

    was_interrupted = False

    try:
        _join_with_keep_alive(keep_alive_output, thread, timeout)
    except KeyboardInterrupt:
        was_interrupted = True

    if (timeout != -1 or was_interrupted) and thread.is_alive():
        assert thread.get_pid() is not None
        result = kill_process(thread.get_pid(), kill_tree, thread, uses_sudo)
        if was_interrupted:
            raise KeyboardInterrupt()
        return result

    if not thread.is_alive():
        exp = thread.exception
        if exp:
            raise exp  # pylint: disable=raising-bad-type

    return thread.returncode, thread.stdout_result, thread.stderr_result


def _join_with_keep_alive(keep_alive_output, thread, timeout):
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
