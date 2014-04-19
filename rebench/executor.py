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

from collections import deque

import logging
import random
import subprocess
import subprocess_with_timeout as subprocess_timeout

from .statistics  import StatisticProperties
from .performance import ExecutionDeliveredNoResults


class RunScheduler(object):

    def __init__(self, executor):
        self._executor = executor

    def execute(self):
        raise NotImplementedError('Subclass responsibility')


class BatchScheduler(RunScheduler):

    def execute(self):
        for run_id in self._executor.runs:
            completed = False
            while not completed:
                completed = self._executor.execute_run(run_id)


class RoundRobinScheduler(RunScheduler):

    def execute(self):
        task_list = deque(self._executor.runs)

        while task_list:
            run = task_list.popleft()
            completed = self._executor.execute_run(run)
            if not completed:
                task_list.append(run)


class RandomScheduler(RunScheduler):

    def execute(self):
        task_list = list(self._executor.runs)

        while task_list:
            run = random.choice(task_list)
            completed = self._executor.execute_run(run)
            if completed:
                task_list.remove(run)


class Executor:
    
    def __init__(self, runs, use_nice, scheduler = BatchScheduler):
        self._runs     = runs
        self._use_nice = use_nice
        self._scheduler = scheduler(self)

        num_runs = len(runs)
        for run in runs:
            run.set_total_number_of_runs(num_runs)
    
    def _construct_cmdline(self, run_id, perf_reader):
        cmdline  = ""
                
        if self._use_nice:
            cmdline += "nice -n-20 "
        
        cmdline += perf_reader.acquire_command(run_id.cmdline())
                
        return cmdline
    
    def execute_run(self, run_id):
        termination_check = run_id.get_termination_check()
        
        run_id.run_config.log()
        run_id.report_start_run()
        
        perf_reader = self._get_performance_reader_instance(
            run_id.bench_cfg.performance_reader)
        
        cmdline = self._construct_cmdline(run_id, perf_reader)
        
        terminate = self._check_termination_condition(run_id, termination_check)
        stats = StatisticProperties(run_id.get_total_values(),
                                    run_id.requested_confidence_level)
        
        # now start the actual execution
        if not terminate:
            terminate = self._generate_data_point(cmdline, perf_reader, run_id,
                                                  termination_check)
            
            stats = StatisticProperties(run_id.get_total_values(),
                                        run_id.requested_confidence_level)
            logging.debug("Run: #%d" % stats.num_samples)

        if terminate:
            run_id.report_run_completed(stats, cmdline)

        return terminate

    @staticmethod
    def _get_performance_reader_instance(reader):
        # depending on how ReBench was executed, the name might one of the two 
        try:
            p = __import__("rebench.performance", fromlist=reader)
        except ImportError:
            p = __import__("performance", fromlist=reader)
        
        return getattr(p, reader)()
        
    def _generate_data_point(self, cmdline, perf_reader, run_id,
                             termination_check):
        # execute the external program here
        (return_code, output, _) = subprocess_timeout.run(cmdline,
                                                          cwd=run_id.bench_cfg.suite.location,
                                                          stdout=subprocess.PIPE,
                                                          stderr=subprocess.STDOUT,
                                                          shell=True,
                                                          timeout=run_id.bench_cfg.suite.max_runtime)
        if return_code != 0:
            run_id.indicate_failed_execution()
            run_id.report_run_failed(cmdline, return_code, output)
            if return_code == 126:
                logging.error(("Could not execute %s. A likely cause is that "
                               "the file is not marked as executable.")
                              % run_id.bench_cfg.vm.name)
        else:
            self._eval_output(output, run_id, perf_reader, cmdline)
        
        return self._check_termination_condition(run_id, termination_check)
    
    def _eval_output(self, output, run_id, perf_reader, cmdline):
        try:
            data_points = perf_reader.parse_data(output, run_id)

            warmup = run_id.warmup_iterations

            for data_point in data_points:
                if warmup > 0:
                    warmup -= 1
                else:
                    run_id.add_data_point(data_point)
                    logging.debug("Run %s:%s result=%s" % (
                        run_id.bench_cfg.vm.name, run_id.bench_cfg.name,
                        data_point.get_total_value()))
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
        for run in self._runs:
            run.report_job_completed(self._runs)

    @property
    def runs(self):
        return self._runs
