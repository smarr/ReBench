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
from __future__ import with_statement, print_function

from collections import deque
from math import floor
import logging
from multiprocessing import cpu_count
import os
import pkgutil
import random
from select import select
import subprocess
import sys
from threading import Thread, RLock

from . import subprocess_with_timeout as subprocess_timeout
from .statistics  import StatisticProperties
from .interop.adapter import ExecutionDeliveredNoResults


class FailedBuilding(Exception):
    """The exception to be raised when building of the VM or suite failed."""
    def __init__(self, name, build_command):
        super(FailedBuilding, self).__init__()
        self._name = name
        self._build_command = build_command


class RunScheduler(object):

    def __init__(self, executor):
        self._executor = executor

    @staticmethod
    def _filter_out_completed_runs(runs):
        return [run for run in runs if not run.is_completed()]

    @staticmethod
    def number_of_uncompleted_runs(runs):
        return len(RunScheduler._filter_out_completed_runs(runs))

    def _process_remaining_runs(self, runs):
        """Abstract, to be implemented"""
        pass

    def execute(self):
        runs = self._filter_out_completed_runs(self._executor.runs)
        self._process_remaining_runs(runs)


class BatchScheduler(RunScheduler):

    def _process_remaining_runs(self, runs):
        for run_id in runs:
            try:
                completed = False
                while not completed:
                    completed = self._executor.execute_run(run_id)
            except FailedBuilding:
                pass


class RoundRobinScheduler(RunScheduler):

    def _process_remaining_runs(self, runs):
        task_list = deque(runs)

        while task_list:
            try:
                run = task_list.popleft()
                completed = self._executor.execute_run(run)
                if not completed:
                    task_list.append(run)
            except FailedBuilding:
                pass


class RandomScheduler(RunScheduler):

    def _process_remaining_runs(self, runs):
        task_list = list(runs)

        while task_list:
            try:
                run = random.choice(task_list)
                completed = self._executor.execute_run(run)
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
        except BaseException as e:
            self.exception = e


class BenchmarkThreadExceptions(Exception):

    def __init__(self, exceptions):
        super(BenchmarkThreadExceptions, self).__init__()
        self.exceptions = exceptions


class ParallelScheduler(RunScheduler):

    def __init__(self, executor, seq_scheduler_class):
        RunScheduler.__init__(self, executor)
        self._seq_scheduler_class = seq_scheduler_class
        self._lock = RLock()
        self._num_worker_threads = self._number_of_threads()
        self._remaining_work = None

    def _number_of_threads(self):
        # TODO: read the configuration elements!
        non_interference_factor = float(2.5)
        return int(floor(cpu_count() / non_interference_factor))

    @staticmethod
    def _split_runs(runs):
        seq_runs = []
        par_runs = []
        for run in runs:
            if run.execute_exclusively:
                seq_runs.append(run)
            else:
                par_runs.append(run)
        return seq_runs, par_runs

    def _process_sequential_runs(self, runs):
        seq_runs, par_runs = self._split_runs(runs)

        scheduler = self._seq_scheduler_class(self._executor)
        scheduler._process_remaining_runs(seq_runs)

        return par_runs

    def _process_remaining_runs(self, runs):
        self._remaining_work = self._process_sequential_runs(runs)

        self._worker_threads = [BenchmarkThread(self, i)
                                for i in range(self._num_worker_threads)]

        for thread in self._worker_threads:
            thread.start()

        exceptions = []
        for thread in self._worker_threads:
            thread.join()
            if thread.exception is not None:
                exceptions.append(thread.exception)

        if exceptions:
            print(exceptions)
            if len(exceptions) == 1:
                raise exceptions[0]
            else:
                raise BenchmarkThreadExceptions(exceptions)

    def _determine_num_work_items_to_take(self):
        # use a simple and naive scheduling strategy that still allows for
        # different running times, without causing too much scheduling overhead
        k = len(self._remaining_work)
        per_thread = int(floor(float(k) / float(self._num_worker_threads)))
        per_thread = max(1, per_thread)  # take at least 1 run
        return per_thread

    def get_local_scheduler(self):
        return self._seq_scheduler_class(self._executor)

    def acquire_work(self):
        with self._lock:
            if not self._remaining_work:
                return None

            n = self._determine_num_work_items_to_take()
            assert n <= len(self._remaining_work)
            work = []
            for _ in range(n):
                work.append(self._remaining_work.pop())
            return work


class Executor(object):

    def __init__(self, runs, use_nice, do_builds, include_faulty=False,
                 verbose=False, scheduler=BatchScheduler, build_log=None):
        self._runs = runs
        self._use_nice = use_nice
        self._do_builds = do_builds
        self._include_faulty = include_faulty
        self._verbose = verbose
        self._scheduler = self._create_scheduler(scheduler)
        self._build_log = build_log

        num_runs = RunScheduler.number_of_uncompleted_runs(runs)
        for run in runs:
            run.set_total_number_of_runs(num_runs)

    def _create_scheduler(self, scheduler):
        # figure out whether to use parallel scheduler
        if cpu_count() > 1:
            i = 0
            for run in self._runs:
                if not run.execute_exclusively:
                    i += 1
            if i > 1:
                return ParallelScheduler(self, scheduler)

        return scheduler(self)

    def _construct_cmdline(self, run_id, gauge_adapter):
        cmdline = ""

        if self._use_nice:
            cmdline += "nice -n-20 "

        cmdline += gauge_adapter.acquire_command(run_id.cmdline())

        return cmdline

    @staticmethod
    def _read(stream):
        data = stream.readline()
        return data.decode('utf-8')

    def _build_vm_and_suite(self, run_id):
        name = "VM:" + run_id.bench_cfg.vm.name
        build = run_id.bench_cfg.vm.build
        self._process_build(build, name, run_id)

        name = "S:" + run_id.bench_cfg.suite.name
        build = run_id.bench_cfg.suite.build
        self._process_build(build, name, run_id)

    def _process_build(self, build, name, run_id):
        if not build or build.is_built:
            return
        if build.is_failed_build:
            run_id.fail_immediately()
            raise FailedBuilding(name, build)
        self._execute_build_cmd(build, name, run_id)

    def _execute_build_cmd(self, build_command, name, run_id):
        path = build_command.location
        if not path or path == ".":
            path = os.getcwd()

        script = build_command.command

        p = subprocess.Popen('/bin/sh', stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             cwd=path)
        p.stdin.write(str.encode(script))
        p.stdin.close()

        if self._build_log:
            with open(self._build_log, 'a') as log_file:
                while True:
                    reads = [p.stdout.fileno(), p.stderr.fileno()]
                    ret = select(reads, [], [])

                    for fd in ret[0]:
                        if fd == p.stdout.fileno():
                            read = self._read(p.stdout)
                            if read:
                                log_file.write(name + '|STD:')
                                log_file.write(read)
                        elif fd == p.stderr.fileno():
                            read = self._read(p.stderr)
                            if read:
                                log_file.write(name + '|ERR:')
                                log_file.write(read)

                    if p.poll() is not None:
                        break
                # read rest of pipes
                while True:
                    read = self._read(p.stdout)
                    if read == "":
                        break
                    log_file.write(name + '|STD:')
                    log_file.write(read)
                while True:
                    read = self._read(p.stderr)
                    if not read:
                        break
                    log_file.write(name + '|ERR:')
                    log_file.write(read)

                log_file.write('\n')

        if p.returncode != 0:
            build_command.mark_failed()
            run_id.fail_immediately()
            run_id.report_run_failed(
                script, p.returncode, "Build of " + name + " failed.")
            raise FailedBuilding(name, build_command)
        else:
            build_command.mark_succeeded()

    def execute_run(self, run_id):
        termination_check = run_id.get_termination_check()

        run_id.run_config.log()
        run_id.report_start_run()

        gauge_adapter = self._get_gauge_adapter_instance(
            run_id.bench_cfg.gauge_adapter)

        cmdline = self._construct_cmdline(run_id, gauge_adapter)

        terminate = self._check_termination_condition(run_id, termination_check)
        if not terminate and self._do_builds:
            self._build_vm_and_suite(run_id)

        stats = StatisticProperties(run_id.get_total_values())

        # now start the actual execution
        if not terminate:
            terminate = self._generate_data_point(cmdline, gauge_adapter,
                                                  run_id, termination_check)

            stats = StatisticProperties(run_id.get_total_values())
            logging.debug("Run: #%d" % stats.num_samples)

        if terminate:
            run_id.report_run_completed(stats, cmdline)

        return terminate

    def _get_gauge_adapter_instance(self, adapter_name):
        adapter_name += "Adapter"

        root = sys.modules['rebench.interop'].__path__

        for _, name, _ in pkgutil.walk_packages(root):
            # depending on how ReBench was executed, name might one of the two
            try:
                p = __import__("rebench.interop." + name, fromlist=adapter_name)
            except ImportError:
                try:
                    p = __import__("interop." + name, fromlist=adapter_name)
                except ImportError:
                    p = None
            if p is not None and hasattr(p, adapter_name):
                return getattr(p, adapter_name)(self._include_faulty)
        return None

    def _generate_data_point(self, cmdline, gauge_adapter, run_id,
                             termination_check):
        print(cmdline)
        # execute the external program here
        (return_code, output, _) = subprocess_timeout.run(
            cmdline, cwd=run_id.location, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, shell=True, verbose=self._verbose,
            timeout=run_id.bench_cfg.suite.max_runtime)
        output = output.decode('utf-8')

        if return_code != 0 and not self._include_faulty:
            run_id.indicate_failed_execution()
            run_id.report_run_failed(cmdline, return_code, output)
            if return_code == 126:
                logging.error(("Could not execute %s. A likely cause is that "
                               "the file is not marked as executable.")
                              % run_id.bench_cfg.vm.name)
        else:
            self._eval_output(output, run_id, gauge_adapter, cmdline)

        return self._check_termination_condition(run_id, termination_check)

    def _eval_output(self, output, run_id, gauge_adapter, cmdline):
        try:
            data_points = gauge_adapter.parse_data(output, run_id)

            warmup = run_id.warmup_iterations

            num_points_to_show = 20
            num_points = len(data_points)
            if num_points > num_points_to_show:
                logging.debug("Skipped %d results..." % (num_points - num_points_to_show))
            i = 0
            for data_point in data_points:
                if warmup > 0:
                    warmup -= 1
                else:
                    run_id.add_data_point(data_point)
                    # only log the last num_points_to_show results
                    if i >= num_points - num_points_to_show:
                        logging.debug("Run %s:%s result=%s" % (
                            run_id.bench_cfg.vm.name, run_id.bench_cfg.name,
                            data_point.get_total_value()))
                i += 1
            run_id.indicate_successful_execution()
        except ExecutionDeliveredNoResults:
            run_id.indicate_failed_execution()
            run_id.report_run_failed(cmdline, 0, output)

    @staticmethod
    def _check_termination_condition(run_id, termination_check):
        return termination_check.should_terminate(
            run_id.get_number_of_data_points())

    def execute(self):
        self._scheduler.execute()
        successful = True
        for run in self._runs:
            run.report_job_completed(self._runs)
            if run.is_failed():
                successful = False
        return successful

    @property
    def runs(self):
        return self._runs
