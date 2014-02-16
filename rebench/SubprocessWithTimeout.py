## Imported from:
##   http://stackoverflow.com/questions/1191374/subprocess-with-timeout
## Includes small modifications STEFAN 2011-01-26

from os import kill
from signal import alarm, signal, SIGALRM, SIGKILL
from subprocess import PIPE, Popen


def run(args, cwd = None, shell = False, kill_tree = True, timeout = -1,
        stdout = PIPE, stderr = PIPE):
    """
    Run a command with a timeout after which it will be forcibly
    killed.
    """
    class Alarm(Exception):
        pass

    def alarm_handler(signum, frame):
        raise Alarm
    
    p = Popen(args, shell=shell, cwd=cwd, stdout=stdout, stderr=stderr)
    if timeout != -1:
        signal(SIGALRM, alarm_handler)
        alarm(timeout)
    try:
        stdout, stderr = p.communicate()
        if timeout != -1:
            alarm(0)
    except Alarm:
        pids = [p.pid]
        if kill_tree:
            pids.extend(get_process_children(p.pid))
        for pid in pids:
            kill(pid, SIGKILL)
        return -9, '', ''
    return p.returncode, stdout, stderr


def get_process_children(pid):
    p = Popen('ps --no-headers -o pid --ppid %d' % pid, shell = True,
              stdout = PIPE, stderr = PIPE)
    stdout, _stderr = p.communicate()
    return [int(p) for p in stdout.split()]
