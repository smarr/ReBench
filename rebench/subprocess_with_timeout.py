from os         import kill
from select     import select
from signal     import SIGKILL
from subprocess import PIPE, STDOUT, Popen
from threading  import Thread
from time       import time

import sys


class SubprocessThread(Thread):

    def __init__(self, binary_name, args, shell, cwd, verbose, stdout, stderr):
        Thread.__init__(self, name = "Subprocess %s" % binary_name)
        self._args    = args
        self._shell   = shell
        self._cwd     = cwd
        self._verbose = verbose
        self._stdout  = stdout
        self._stderr  = stderr

        self.stdout_result = None
        self.stderr_result = None
        self.returncode    = None
        self.pid           = None

    def run(self):
        p = Popen(self._args, shell=self._shell, cwd=self._cwd,
                  stdout=self._stdout, stderr=self._stderr)
        self.pid = p.pid

        self.process_output(p)
        self.returncode = p.returncode

    def process_output(self, p):
        if self._verbose and self._stdout == PIPE and (self._stderr == PIPE or
                                                       self._stderr == STDOUT):
            self.stdout_result = ""
            self.stderr_result = ""

            while True:
                reads = [p.stdout.fileno()]
                if self._stderr == PIPE:
                    reads.append(p.stderr.fileno())
                ret = select(reads, [], [])

                for fd in ret[0]:
                    if fd == p.stdout.fileno():
                        read = p.stdout.readline()
                        sys.stdout.write(read)
                        self.stdout_result += read
                    if self._stderr == PIPE and fd == p.stderr.fileno():
                        read = p.stderr.readline()
                        sys.stderr.write(read)
                        self.stderr_result += read

                if p.poll() is not None:
                    break
        else:
            self.stdout_result, self.stderr_result = p.communicate()


def run(args, cwd = None, shell = False, kill_tree = True, timeout = -1,
        verbose = False, stdout = PIPE, stderr = PIPE):
    """
    Run a command with a timeout after which it will be forcibly
    killed.
    """
    binary_name = args.split(' ')[0]

    thread = SubprocessThread(binary_name, args, shell, cwd, verbose, stdout,
                              stderr)
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
                    t = t10min
                else:
                    t = timeout - diff
                thread.join(t)
                if not thread.is_alive():
                    break
                diff = time() - start
                if diff < timeout:
                    print "Keep alive, current job runs for %dmin" % (diff / 60)

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

