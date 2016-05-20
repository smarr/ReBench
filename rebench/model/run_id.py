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
import logging
import re
import sys

from .benchmark_config import BenchmarkConfig


class RunId(object):

    def __init__(self, bench_cfg, cores, input_size, var_value):
        self._bench_cfg   = bench_cfg
        self._cores       = cores
        self._input_size  = input_size
        self._var_value   = var_value

        self._reporters   = set()
        self._persistence = set()
        self._requested_confidence_level = 0
        self._run_config  = None
        self._data_points = []

        self._termination_check = None
        self._cmdline = None

    def requires_warmup(self):
        return self._bench_cfg.warmup_iterations > 0

    @property
    def warmup_iterations(self):
        return self._bench_cfg.warmup_iterations

    @property
    def execute_exclusively(self):
        return self._bench_cfg.execute_exclusively

    def indicate_failed_execution(self):
        self._termination_check.indicate_failed_execution()

    def indicate_successful_execution(self):
        self._termination_check.indicate_successful_execution()

    def add_reporter(self, reporter):
        self._reporters.add(reporter)

    def add_reporting(self, reporting):
        self._reporters.update(reporting.get_reporters())
        self._requested_confidence_level = max(reporting.confidence_level,
                                               self._requested_confidence_level)

    def report_run_failed(self, cmdline, return_code, output):
        for reporter in self._reporters:
            reporter.run_failed(self, cmdline, return_code, output)

    def report_run_completed(self, statistics, cmdline):
        for reporter in self._reporters:
            reporter.run_completed(self, statistics, cmdline)

    def report_job_completed(self, run_ids):
        for reporter in self._reporters:
            reporter.job_completed(run_ids)

    def set_total_number_of_runs(self, num_runs):
        for reporter in self._reporters:
            reporter.set_total_number_of_runs(num_runs)

    def report_start_run(self):
        for reporter in self._reporters:
            reporter.start_run(self)

    def add_persistence(self, persistence):
        self._persistence.add(persistence)

    def loaded_data_point(self, data_point):
        self._data_points.append(data_point)

    def add_data_point(self, data_point):
        self._data_points.append(data_point)
        for persistence in self._persistence:
            persistence.persist_data_point(data_point)
    
    def get_number_of_data_points(self):
        return len(self._data_points)
    
    def get_data_points(self):
        return self._data_points

    def get_total_values(self):
        return [dp.get_total_value() for dp in self._data_points]
    
    def set_run_config(self, run_cfg):
        if self._run_config and self._run_config != run_cfg:
            raise ValueError("Run config has already been set "
                             "and is not the same.")
        self._run_config = run_cfg
    
    def get_termination_check(self):
        if self._termination_check is None:
            self._termination_check = self._run_config.create_termination_check(
                self._bench_cfg)
        return self._termination_check

    def is_completed(self):
        """ Check whether the termination condition is satisfied. """
        return self.get_termination_check().should_terminate(
            self.get_number_of_data_points())

    def run_failed(self):
        return (self._termination_check.fails_consecutively() or
                self._termination_check.has_too_many_failures(
                    len(self._data_points)))

    @property
    def run_config(self):
        return self._run_config
    
    @property
    def requested_confidence_level(self):
        return self._requested_confidence_level
    
    @property
    def bench_cfg(self):
        return self._bench_cfg
    
    @property
    def cores(self):
        return self._cores

    @property
    def input_size(self):
        return self._input_size

    @property
    def cores_as_str(self):
        return '' if self._cores is None else str(self._cores)

    @property
    def input_size_as_str(self):
        return '' if self._input_size is None else str(self._input_size)

    @property
    def var_value_as_str(self):
        return '' if self._var_value is None else str(self._var_value)

    @property
    def var_value(self):
        return self._var_value
    
    def __hash__(self):
        return hash(self.cmdline())

    def as_simple_string(self):
        return "%s %s %s %s" % (self._bench_cfg.as_simple_string(),
                                self._cores, self._input_size, self._var_value)

    def _expand_vars(self, string):
        return string % {'benchmark' : self._bench_cfg.command,
                         'input'     : self._input_size,
                         'variable'  : self._var_value,
                         'cores'     : self._cores,
                         'warmup'    : self._bench_cfg.warmup_iterations
                        }

    def cmdline(self):
        if self._cmdline:
            return self._cmdline

        cmdline = ""
        vm_cmd  = "%s/%s %s" % (self._bench_cfg.vm.path,
                                self._bench_cfg.vm.binary,
                                self._bench_cfg.vm.args)

        cmdline += vm_cmd 
        cmdline += self._bench_cfg.suite.command
        
        if self._bench_cfg.extra_args is not None:
            cmdline += " %s" % self._bench_cfg.extra_args
            
        try:
            cmdline = self._expand_vars(cmdline)
        except ValueError:
            self._report_cmdline_format_issue_and_exit(cmdline)
        except TypeError:
            self._report_cmdline_format_issue_and_exit(cmdline)
        
        self._cmdline = cmdline.strip()
        return self._cmdline

    @property
    def location(self):
        return self._expand_vars(self._bench_cfg.suite.location)

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
            and self.cmdline() == other.cmdline())

    def __ne__(self, other):
        return not self.__eq__(other)
    
    def _report_cmdline_format_issue_and_exit(self, cmdline):
        logging.critical("The configuration of %s contains improper "
                         "Python format strings.", self._bench_cfg.name)
         
        # figure out which format misses a conversion type
        without_conversion_type = re.findall("\%\(.*?\)(?![diouxXeEfFgGcrs\%])", cmdline)
        logging.error("The command line configured is: %s", cmdline)
        logging.error("The following elements do not have conversion types: \"%s\"",
                      '", "'.join(without_conversion_type))
        logging.error("This can be fixed by replacing for instance %s with %ss",
                      without_conversion_type[0],
                      without_conversion_type[0])
        sys.exit(-1)

    def as_str_list(self):
        result = self._bench_cfg.as_str_list()

        result.append(self.cores_as_str)
        result.append(self.input_size_as_str)
        result.append(self.var_value_as_str)

        return result

    @classmethod
    def from_str_list(cls, data_store, str_list):
        bench_cfg = BenchmarkConfig.from_str_list(data_store, str_list[:-3])
        return data_store.create_run_id(
            bench_cfg, str_list[-3], str_list[-2], str_list[-1])

    def __str__(self):
        return "RunId(%s, %s, %s, %s, %s, %d)" % (self._bench_cfg.name,
                                                  self._cores,
                                                  self._bench_cfg.extra_args,
                                                  self._input_size or '',
                                                  self._var_value  or '',
                                                  self._bench_cfg.warmup_iterations)
