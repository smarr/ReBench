# Copyright (c) 2009-2014 Stefan Marr <http://www.stefan-marr.de/>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
from time import time
import logging


class RunsConfig(object):
    """ General configuration parameters for runs """
    def __init__(self,
                 number_of_data_points = None,
                 min_runtime           = None,
                 parallel_interference_factor = 2.5):
        self._number_of_data_points = number_of_data_points
        self._min_runtime           = min_runtime
        self._parallel_interference_factor = parallel_interference_factor
    
    @property
    def number_of_data_points(self):
        return self._number_of_data_points
        
    @property
    def min_runtime(self):
        return self._min_runtime

    @property
    def parallel_interference_factor(self):
        return self._parallel_interference_factor
        
    def combined(self, run_def):
        config = RunsConfig(self._number_of_data_points, self._min_runtime,
                            self._parallel_interference_factor)
        val = run_def.get('number_of_data_points', None)
        if val:
            config._number_of_data_points = val
        val = run_def.get('min_runtime', None)
        if val:
            config._min_runtime = val
        # parallel_interference_factor is a global setting, so it is not
        # merged from other run definitions
        return config
    
    def log(self):
        msg = "Run Config: number of data points: %d" % self._number_of_data_points
        if self._min_runtime:
            msg += ", min_runtime: %dms" % self._min_runtime
        logging.debug(msg)
    
    def create_termination_check(self, bench_cfg):
        return TerminationCheck(self, bench_cfg)


class QuickRunsConfig(RunsConfig):
    
    def __init__(self, number_of_data_points = None,
                       min_runtime           = None,
                       max_time              = None):
        super(QuickRunsConfig, self).__init__(number_of_data_points,
                                              min_runtime)
        self._max_time = max_time
    
    def combined(self, run_def):
        """For Quick runs, only the global config is taken into account.""" 
        return self
    
    @property
    def max_time(self):
        return self._max_time
    
    def create_termination_check(self, bench_cfg):
        return QuickTerminationCheck(self, bench_cfg)


class TerminationCheck(object):
    def __init__(self, run_cfg, bench_cfg):
        self._run_cfg   = run_cfg
        self._bench_cfg = bench_cfg
        self._consecutive_erroneous_executions = 0
        self._failed_execution_count = 0

    def indicate_failed_execution(self):
        self._consecutive_erroneous_executions += 1
        self._failed_execution_count           += 1

    def indicate_successful_execution(self):
        self._consecutive_erroneous_executions = 0

    def has_sufficient_number_of_data_points(self, number_of_data_points):
        return number_of_data_points >= self._run_cfg.number_of_data_points

    def fails_consecutively(self):
        return self._consecutive_erroneous_executions >= 3

    def has_too_many_failures(self, number_of_data_points):
        return ((self._failed_execution_count > 6) or (
                number_of_data_points > 10 and (
                    self._failed_execution_count > number_of_data_points / 2)))

    def should_terminate(self, number_of_data_points):
        if self.has_sufficient_number_of_data_points(number_of_data_points):
            logging.debug("Reached number_of_data_points for %s"
                          % self._bench_cfg.name)
            return True
        elif self.fails_consecutively():
            logging.error(("Three executions of %s have failed in a row, " +
                          "benchmark is aborted") % self._bench_cfg.name)
            return True
        elif self.has_too_many_failures(number_of_data_points):
            logging.error("Many runs of %s are failing, benchmark is aborted."
                          % self._bench_cfg.name)
            return True
        else:
            return False


class QuickTerminationCheck(TerminationCheck):
    def __init__(self, run_cfg, bench_cfg):
        super(QuickTerminationCheck, self).__init__(run_cfg, bench_cfg)
        self._start_time = time()
    
    def should_terminate(self, number_of_data_points):
        if time() - self._start_time > self._run_cfg.max_time:
            logging.debug("Maximum runtime is reached for %s" % self._run_cfg.name)
            return True
        return super(QuickTerminationCheck, self).should_terminate(
            number_of_data_points)
