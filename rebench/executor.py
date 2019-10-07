# Copyright (c) 2009-2014 Stefan Marr <http://www.stefan-marr.de/>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
from __future__ import with_statement

from codecs import open as open_with_enc
from collections import deque
from math import floor
from threading import Thread, RLock, Event

import time
import os
import pkgutil
import random
import sys
import errno
import subprocess32 as subprocess

from .interop.adapter import ExecutionDeliveredNoResults
from .ui import escape_braces
from .configurator import cpu_count, can_parallelize


def make_subprocess_runner():
    # subprocess.run is superb, but we do not have access
    # to the processes objects in case we need to kill them...
    # (stripped to whats needed here)

    meta = (set(), RLock()) # poor man's closure
    def _put(what):
        with meta[1]:#lock
            meta[0].add(what)#set
    def _pop(what):
        with meta[1]:#lock
            meta[0].discard(what) #set
    def _walk(fun, *args, **kwargs):
        with meta[1]:#lock
            fun(meta[0], *args, **kwargs)#set
    def _run(*args, **kwargs):
        input = kwargs.pop('input', None)
        timeout = kwargs.pop('timeout', None)
        if input is not None:
            assert not 'stdin' in kwargs
            kwargs['stdin'] = subprocess.PIPE
        with subprocess.Popen(*args, **kwargs) as process:
            try:
                _put(process)
                stdout, stderr = process.communicate(input, timeout=timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                raise subprocess.TimeoutExpired(process.args, timeout, output=stdout,
                                     stderr=stderr)
            except:
                process.kill()
                process.wait()
                raise
            finally:
                _pop(process)
            retcode = process.poll()
        return subprocess.CompletedProcess(process.args, retcode, stdout, stderr)
    return _run, _walk
subprocess_run, walk_processes = make_subprocess_runner()

def terminate_processes():
    def _signal(procs):
        for proc in procs:
            if proc is not None and proc.poll() is None:
                proc.kill()
    walk_processes(_signal)

from humanfriendly.compat import coerce_string, is_unicode
def _maybe_decode(what):
    if not is_unicode(what):
        return coerce_string(what.decode('utf-8'))
    return what



class FailedBuilding(Exception):
    """The exception to be raised when building of the executor or suite failed."""
    def __init__(self, name, build_command):
        super(FailedBuilding, self).__init__()
        self._name = name
        self._build_command = build_command


class RunScheduler(object):

    def __init__(self, executor, ui):
        self._executor = executor
        self._ui = ui
        self._runs_completed = 0
        self._start_time = time.time()
        self._total_num_runs = 0

    @staticmethod
    def _filter_out_completed_runs(runs, ui):
        return [run for run in runs if not run.is_completed(ui)]

    @staticmethod
    def number_of_uncompleted_runs(runs, ui):
        return len(RunScheduler._filter_out_completed_runs(runs, ui))

    def _process_remaining_runs(self, runs):
        raise NotImplementedError("abstract base class")

    def _estimate_time_left(self):
        if self._runs_completed == 0:
            return 0, 0, 0

        current = time.time()
        time_per_invocation = ((current - self._start_time) / self._runs_completed)
        etl = time_per_invocation * (self._total_num_runs - self._runs_completed)
        sec = etl % 60
        minute = (etl - sec) / 60 % 60
        hour = (etl - sec - minute) / 60 / 60
        return floor(hour), floor(minute), floor(sec)

    def _indicate_progress(self, completed_task, run):
        if not self._ui.spinner_initialized():
            return

        if completed_task:
            self._runs_completed += 1

        art_mean = run.get_mean_of_totals()

        hour, minute, sec = self._estimate_time_left()

        label = "Running Benchmarks: %70s\tmean: %10.1f\ttime left: %02d:%02d:%02d" \
                % (run.as_simple_string(), art_mean, hour, minute, sec)
        self._ui.step_spinner(self._runs_completed, label)

    def indicate_build(self, run_id):
        run_id_names = run_id.as_str_list()
        self._ui.step_spinner(
            self._runs_completed, "Run build for %s %s" % (run_id_names[1], run_id_names[2]))

    def execute(self):
        self._total_num_runs = len(self._executor.runs)
        runs = self._filter_out_completed_runs(self._executor.runs, self._ui)
        completed_runs = self._total_num_runs - len(runs)
        self._runs_completed = completed_runs

        with self._ui.init_spinner(self._total_num_runs):
            self._ui.step_spinner(completed_runs)
            self._process_remaining_runs(runs)

    @classmethod
    def as_sequential(cls, executor, ui):
        return cls(executor, ui)

    @classmethod
    def as_parallel(cls, executor, ui):
        return ParallelScheduler(executor, cls, ui)

class BatchScheduler(RunScheduler):

    def _process_remaining_runs(self, runs):
        for run_id in runs:
            try:
                completed = False
                while not completed:
                    completed = self._executor.execute_run(run_id)
                    self._indicate_progress(completed, run_id)
            except FailedBuilding:
                pass


class RoundRobinScheduler(RunScheduler):

    def _process_remaining_runs(self, runs):
        task_list = deque(runs)

        while task_list:
            try:
                run = task_list.popleft()
                completed = self._executor.execute_run(run)
                self._indicate_progress(completed, run)
                if not completed:
                    task_list.append(run)
            except FailedBuilding:
                pass


class RandomScheduler(RunScheduler):

    def _process_remaining_runs(self, runs):
        task_list = list(runs)

        while task_list:
            run = random.choice(task_list)
            try:
                completed = self._executor.execute_run(run)
                self._indicate_progress(completed, run)
                if completed:
                    task_list.remove(run)
            except FailedBuilding:
                task_list.remove(run)


class BenchmarkThread(Thread):

    def __init__(self, par_scheduler, num):
        Thread.__init__(self, name="BenchmarkThread %d" % num)
        self._par_scheduler = par_scheduler
        self._id = num
        self.exception = None

    def run(self):
        try:
            scheduler = self._par_scheduler.get_local_scheduler()

            while True:
                work = self._par_scheduler.acquire_work()
                if work is None:
                    return
                scheduler._process_remaining_runs(work)
        except BaseException as exp:
            self.exception = exp


class BenchmarkThreadExceptions(Exception):

    def __init__(self, exceptions):
        super(BenchmarkThreadExceptions, self).__init__()
        self.exceptions = exceptions

class BaseParallelScheduler(RunScheduler):
    def __init__(self, executor, ui):
        super(BaseParallelScheduler, self).__init__(executor, ui)
        self._worker_count = self._number_of_threads()

    @classmethod
    def _number_of_threads(cls):
        # TODO: read the configuration elements!
        non_interference_factor = float(2.5)
        # make sure we have at least one thread
        return max(1, int(floor(cpu_count() / non_interference_factor)))

    @classmethod
    def _split_runs(cls, runs):
        seq_runs = []
        par_runs = []
        for run in runs:
            if run.execute_exclusively:
                seq_runs.append(run)
            else:
                par_runs.append(run)
        return seq_runs, par_runs

    def _process_remaining_runs(self, runs):
        seq_runs, par_runs = self._split_runs(runs)
        self._process_sequential_runs(seq_runs)
        self._process_parallel_runs(par_runs)

    def _process_sequential_runs(self, seq_runs):
        raise NotImplementedError("abstract base class")
    def _process_parallel_runs(self, seq_runs):
        raise NotImplementedError("abstract base class")


class ParallelScheduler(BaseParallelScheduler):

    def __init__(self, executor, seq_scheduler_class, ui):
        super(ParallelScheduler, self).__init__(executor, ui)
        self._seq_scheduler_class = seq_scheduler_class
        self._lock = RLock()
        self._remaining_work = None
        self._worker_threads = None


    def _process_sequential_runs(self, seq_runs):
        scheduler = self._seq_scheduler_class(self._executor, self._ui)
        scheduler._process_remaining_runs(seq_runs)

    def _process_parallel_runs(self, par_runs):
        self._remaining_work = self.par_runs

        self._worker_threads = [BenchmarkThread(self, i)
                                for i in range(self._worker_count)]

        for thread in self._worker_threads:
            thread.start()

        exceptions = []
        for thread in self._worker_threads:
            thread.join()
            if thread.exception is not None:
                exceptions.append(thread.exception)

        if exceptions:
            if len(exceptions) == 1:
                raise exceptions[0]
            raise BenchmarkThreadExceptions(exceptions)

    def _determine_num_work_items_to_take(self):
        # use a simple and naive scheduling strategy that still allows for
        # different running times, without causing too much scheduling overhead
        k = len(self._remaining_work)
        per_thread = int(floor(float(k) / float(self._worker_count)))
        per_thread = max(1, per_thread)  # take at least 1 run
        return per_thread

    def get_local_scheduler(self):
        return self._seq_scheduler_class(self._executor, self._ui)

    def acquire_work(self):
        with self._lock:
            if not self._remaining_work:
                return None

            num = self._determine_num_work_items_to_take()
            assert num <= len(self._remaining_work)
            work = []
            for _ in range(num):
                work.append(self._remaining_work.pop())
            return work

class PullingScheduler(BatchScheduler):
    # same as superclass, but different parallel counterpart
    @classmethod
    def as_parallel(cls, executor, ui):
        return PullingParallelScheduler(executor, ui)

class PullingParallelScheduler(BaseParallelScheduler):

    def __init__(self, executor, ui):
        super(PullingParallelScheduler, self).__init__(executor, ui)
        self._work = self._new_queue()
        self._should_stop = Event()

    def _new_queue(self):
        try:
            import Queue as queue
        except ImportError:
            import queue
        return queue.Queue()

    def _process_sequential_runs(self, seq_runs):
        scheduler = self.as_sequential(self._executor, self._ui)
        scheduler._process_remaining_runs(seq_runs)

    def _execute_one_run(self, run_id):
        completed = False
        try:
            completed = self._executor.execute_run(run_id)
            self._indicate_progress(completed, run_id)
        except FailedBuilding:
            pass
        return completed

    def _pull_and_execute(self, exceptions):
        while not self._should_stop.is_set():
            completed = False
            run_id = self._work.get()
            try:
                if run_id is None:
                    return
                completed = self._execute_one_run(run_id)
                if not completed:
                    self._work.put(run_id)
            except BaseException as exp:
                exceptions.append(exp)
            finally:
                self._work.task_done()


    def _process_parallel_runs(self, par_runs):
        for run in par_runs:
            self._work.put(run)
        exceptions = []
        self._process_work(exceptions)
        if exceptions:
            raise (exceptions[0] if len(exceptions) == 1 \
                   else BenchmarkThreadExceptions(exceptions))

    def _2_process_work(self, exceptions):
        workers = [Thread(target=self._pull_and_execute, args=(exceptions,))
                   for _ in range(self._worker_count)]
        for worker in workers:
            worker.daemon = True
            worker.start()
        try:
            self._work.join()
        except KeyboardInterrupt:
            self._should_stop.set()
            raise
        for _ in range(self._worker_count): self._work.put(None)



    def _3_process_work(self, exceptions):
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self._worker_count) as executor:
            for _ in range(self._worker_count):
                executor.submit(self._pull_and_execute, exceptions)
            try:
                self._work.join()
            except KeyboardInterrupt:
                self._should_stop.set()
                raise
            for _ in range(self._worker_count): self._work.put(None)

    if sys.version_info < (3, 3):
        _process_work =  _2_process_work
    else:
        _process_work =  _3_process_work

    @classmethod
    def as_sequential(cls, executor, ui):
        return PullingScheduler(executor, ui)

class Executor(object):

    def __init__(self, runs, use_nice, do_builds, ui, include_faulty=False,
                 debug=False, scheduler=BatchScheduler, build_log=None):
        self._runs = runs
        self._use_nice = use_nice
        self._do_builds = do_builds
        self._ui = ui
        self._include_faulty = include_faulty
        self._debug = debug
        self._scheduler = self._create_scheduler(scheduler)
        self._build_log = build_log

        num_runs = RunScheduler.number_of_uncompleted_runs(runs, ui)
        for run in runs:
            run.set_total_number_of_runs(num_runs)

    def _create_scheduler(self, scheduler):
        # figure out whether to use parallel scheduler
        if (can_parallelize() and
            any(not run.execute_exclusively for run in self._runs)):
            return scheduler.as_parallel(self, self._ui)
        return scheduler.as_sequential(self, self._ui)

    def _construct_cmdline(self, run_id, gauge_adapter):
        cmdline = ""

        if self._use_nice:
            cmdline += "nice -n-20 "

        cmdline += gauge_adapter.acquire_command(run_id.cmdline())

        return cmdline

    @staticmethod
    def _read(stream):
        data = stream.readline()
        decoded = data.decode('utf-8')
        return coerce_string(decoded)

    def _build_executor_and_suite(self, run_id):
        name = "E:" + run_id.benchmark.suite.executor.name
        build = run_id.benchmark.suite.executor.build
        self._process_builds(build, name, run_id)

        name = "S:" + run_id.benchmark.suite.name
        build = run_id.benchmark.suite.build
        self._process_builds(build, name, run_id)

    def _process_builds(self, builds, name, run_id):
        if not builds:
            return

        for build in builds:
            if build.is_built:
                continue

            if build.is_failed_build:
                run_id.fail_immediately()
                raise FailedBuilding(name, build)
            self._execute_build_cmd(build, name, run_id)

    def _execute_build_cmd(self, build_command, name, run_id):
        path = build_command.location
        if not path or path == ".":
            path = os.getcwd()

        script = build_command.command

        self._scheduler.indicate_build(run_id)
        self._ui.debug_output_info("Start build\n", None, script, path)

        try:
            result = subprocess_run('/bin/sh',
                cwd=path,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                shell=False, input=script.encode('utf-8'))
        except OSError as err:
            build_command.mark_failed()
            run_id.fail_immediately()
            run_id.report_run_failed(
                script, err.errno, "Build of " + name + " failed.")

            if err.errno == 2:
                msg = ("{ind}Build of %s failed.\n"
                       + "{ind}{ind}It failed with: %s.\n"
                       + "{ind}{ind}File name: %s\n") % (name, err.strerror, err.filename)
            else:
                msg = str(err)
            self._ui.error(msg, run_id, script, path)
            return

        stdout_result = _maybe_decode(result.stdout)
        stderr_result = _maybe_decode(result.stderr)

        if self._build_log:
            self.process_output(name, stdout_result, stderr_result)

        if result.returncode != 0:
            build_command.mark_failed()
            run_id.fail_immediately()
            run_id.report_run_failed(
                script, result.returncode, "Build of " + name + " failed.")
            self._ui.error("{ind}Build of " + name + " failed.\n", None, script, path)
            if stdout_result and stdout_result.strip():
                lines = escape_braces(stdout_result).split('\n')
                self._ui.error("{ind}stdout:\n\n{ind}{ind}"
                               + "\n{ind}{ind}".join(lines) + "\n")
            if stderr_result and stderr_result.strip():
                lines = escape_braces(stderr_result).split('\n')
                self._ui.error("{ind}stderr:\n\n{ind}{ind}"
                               + "\n{ind}{ind}".join(lines) + "\n")
            raise FailedBuilding(name, build_command)

        build_command.mark_succeeded()

    def process_output(self, name, stdout_result, stderr_result):
        with open_with_enc(self._build_log, 'a', encoding='utf8') as log_file:
            if stdout_result:
                log_file.write(name + '|STD:')
                log_file.write(stdout_result)
            if stderr_result:
                log_file.write(name + '|ERR:')
                log_file.write(stderr_result)

    def execute_run(self, run_id):
        termination_check = run_id.get_termination_check(self._ui)

        run_id.report_start_run()

        gauge_adapter = self._get_gauge_adapter_instance(
            run_id.benchmark.gauge_adapter)

        cmdline = self._construct_cmdline(run_id, gauge_adapter)

        terminate = self._check_termination_condition(run_id, termination_check)
        if not terminate and self._do_builds:
            self._build_executor_and_suite(run_id)

        # now start the actual execution
        if not terminate:
            terminate = self._generate_data_point(cmdline, gauge_adapter,
                                                  run_id, termination_check)

        mean_of_totals = run_id.get_mean_of_totals()
        if terminate:
            run_id.report_run_completed(cmdline)
            if (not run_id.is_failed() and run_id.min_iteration_time
                    and mean_of_totals < run_id.min_iteration_time):
                self._ui.warning(
                    ("{ind}Warning: Low mean run time.\n"
                     + "{ind}{ind}The mean (%.1f) is lower than min_iteration_time (%d)\n")
                    % (mean_of_totals, run_id.min_iteration_time), run_id, cmdline)

        return terminate

    def _get_gauge_adapter_instance(self, adapter_name):
        adapter_name += "Adapter"

        root = sys.modules['rebench.interop'].__path__

        for _, name, _ in pkgutil.walk_packages(root):
            # depending on how ReBench was executed, name might one of the two
            try:
                mod = __import__("rebench.interop." + name, fromlist=adapter_name)
            except ImportError:
                try:
                    mod = __import__("interop." + name, fromlist=adapter_name)
                except ImportError:
                    mod = None
            if mod is not None and hasattr(mod, adapter_name):
                return getattr(mod, adapter_name)(self._include_faulty)
        return None

    def _generate_data_point(self, cmdline, gauge_adapter, run_id,
                             termination_check):
        # execute the external program here
        timed_out = False
        try:
            self._ui.debug_output_info("{ind}Starting run\n", run_id, cmdline)
            result = subprocess_run(
                cmdline, cwd=run_id.location, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=True, timeout=run_id.max_invocation_time,
                start_new_session=True)
            output = _maybe_decode(result.stdout)
            return_code = result.returncode
        except OSError as err:
            run_id.fail_immediately()
            if err.errno == 2:
                msg = ("{ind}Failed executing run\n"
                       + "{ind}{ind}It failed with: %s.\n"
                       + "{ind}{ind}File name: %s\n") % (err.strerror, err.filename)
            else:
                msg = str(err)
            self._ui.error(msg, run_id, cmdline)
            return True
        except subprocess.TimeoutExpired as expired:
            timed_out = True
            output = _maybe_decode(expired.stdout)
            return_code = errno.ETIME

        if return_code != 0 and not self._include_faulty and not (
                timed_out and run_id.ignore_timeouts):
            run_id.indicate_failed_execution()
            run_id.report_run_failed(cmdline, return_code, output)
            if return_code == 126:
                msg = ("{ind}Error: Could not execute %s.\n"
                       + "{ind}{ind}The file may not be marked as executable.\n"
                       + "{ind}Return code: %d\n") % (
                           run_id.benchmark.suite.executor.name, return_code)
            elif timed_out:
                msg = ("{ind}Run timed out.\n"
                       + "{ind}{ind}Return code: %d\n"
                       + "{ind}{ind}max_invocation_time: %s\n") % (
                           return_code, run_id.max_invocation_time)
            else:
                msg = "{ind}Run failed. Return code: %d\n" % return_code

            self._ui.error(msg, run_id, cmdline)

            if output and output.strip():
                lines = escape_braces(output).split('\n')
                self._ui.error("{ind}Output:\n\n{ind}{ind}"
                               + "\n{ind}{ind}".join(lines) + "\n")
        else:
            self._eval_output(output, run_id, gauge_adapter, cmdline)

        return self._check_termination_condition(run_id, termination_check)

    def _eval_output(self, output, run_id, gauge_adapter, cmdline):
        try:
            data_points = gauge_adapter.parse_data(output, run_id, run_id.completed_invocations + 1)

            warmup = run_id.warmup_iterations

            num_points_to_show = 20
            num_points = len(data_points)

            msg = "{ind}Completed invocation\n"

            if num_points > num_points_to_show:
                msg += "{ind}{ind}Recorded %d data points, show last 20...\n" % num_points
            i = 0
            for data_point in data_points:
                if warmup is not None and warmup > 0:
                    warmup -= 1
                    run_id.add_data_point(data_point, True)
                else:
                    run_id.add_data_point(data_point, False)
                    # only log the last num_points_to_show results
                    if i >= num_points - num_points_to_show:
                        msg += "{ind}{ind}%4d\t%s%s\n" % (
                            i + 1, data_point.get_total_value(), data_point.get_total_unit())
                i += 1

            run_id.indicate_successful_execution()
            self._ui.verbose_output_info(msg, run_id, cmdline)
        except ExecutionDeliveredNoResults:
            run_id.indicate_failed_execution()
            run_id.report_run_failed(cmdline, 0, output)

    @staticmethod
    def _check_termination_condition(run_id, termination_check):
        return termination_check.should_terminate(
            run_id.get_number_of_data_points())

    def execute(self):
        try:
            self._scheduler.execute()
            successful = True
            for run in self._runs:
                run.report_job_completed(self._runs)
                if run.is_failed():
                    successful = False
            return successful
        finally:
            for run in self._runs:
                run.close_files()

    @property
    def runs(self):
        return self._runs
