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
import re

from .benchmark import Benchmark
from .termination_check import TerminationCheck
from ..statistics import StatisticProperties
from ..ui import UIError


class RunId(object):

    def __init__(self, benchmark, cores, input_size, var_value):
        self._benchmark = benchmark
        self._cores = cores
        self._input_size = input_size
        self._var_value = var_value

        self._reporters = set()
        self._persistence = set()
        self._statistics = StatisticProperties()
        self._total_unit = None

        self._termination_check = None
        self._cmdline = None
        self._failed = True

        self._max_invocation = 0

    @property
    def warmup_iterations(self):
        return self._benchmark.run_details.warmup

    @property
    def min_iteration_time(self):
        return self._benchmark.run_details.min_iteration_time

    @property
    def max_invocation_time(self):
        return self._benchmark.run_details.max_invocation_time

    @property
    def ignore_timeouts(self):
        return self._benchmark.run_details.ignore_timeouts

    @property
    def retries_after_failure(self):
        return self._benchmark.run_details.retries_after_failure

    @property
    def iterations(self):
        run_details = self._benchmark.run_details
        if run_details.iterations_override is not None:
            return run_details.iterations_override
        return run_details.iterations

    @property
    def invocations(self):
        run_details = self._benchmark.run_details
        if run_details.invocations_override is not None:
            return run_details.invocations_override
        return run_details.invocations

    @property
    def completed_invocations(self):
        return self._max_invocation

    @property
    def execute_exclusively(self):
        return self._benchmark.run_details.execute_exclusively

    @property
    def benchmark(self):
        return self._benchmark

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

    @property
    def location(self):
        if not self._benchmark.suite.location:
            return None
        return self._expand_vars(self._benchmark.suite.location)

    def build_commands(self):
        commands = set()
        builds = self._benchmark.suite.executor.build
        if builds:
            commands.update(builds)
        builds = self._benchmark.suite.build
        if builds:
            commands.update(builds)
        return commands

    def requires_warmup(self):
        return self._benchmark.run_details.warmup > 0

    def fail_immediately(self):
        self._termination_check.fail_immediately()

    def indicate_failed_execution(self):
        self._termination_check.indicate_failed_execution()

    def indicate_successful_execution(self):
        self._failed = False
        self._termination_check.indicate_successful_execution()

    def is_failed(self):
        return self._failed

    def add_reporter(self, reporter):
        self._reporters.add(reporter)

    def add_reporting(self, reporting):
        self._reporters.update(reporting.get_reporters())

    def report_run_failed(self, cmdline, return_code, output):
        for reporter in self._reporters:
            reporter.run_failed(self, cmdline, return_code, output)

    def report_run_completed(self, cmdline):
        for reporter in self._reporters:
            reporter.run_completed(self, self._statistics, cmdline)
        for persistence in self._persistence:
            persistence.run_completed()

    def report_job_completed(self, run_ids):
        for reporter in self._reporters:
            reporter.job_completed(run_ids)

    def set_total_number_of_runs(self, num_runs):
        for reporter in self._reporters:
            reporter.set_total_number_of_runs(num_runs)

    def report_start_run(self):
        for reporter in self._reporters:
            reporter.start_run(self)

    def is_persisted_by(self, persistence):
        return persistence in self._persistence

    def add_persistence(self, persistence):
        self._persistence.add(persistence)

    def close_files(self):
        for persistence in self._persistence:
            persistence.close()

    def _new_data_point(self, data_point, warmup):
        self._max_invocation = max(self._max_invocation, data_point.invocation)
        if self._total_unit is None:
            self._total_unit = data_point.get_total_unit()
        if not warmup:
            self._statistics.add_sample(data_point.get_total_value())

    def loaded_data_point(self, data_point, warmup):
        for persistence in self._persistence:
            persistence.loaded_data_point(data_point)
        self._new_data_point(data_point, warmup)

    def add_data_point(self, data_point, warmup):
        self._new_data_point(data_point, warmup)

        for persistence in self._persistence:
            persistence.persist_data_point(data_point)

    def get_number_of_data_points(self):
        return self._statistics.num_samples

    def get_mean_of_totals(self):
        return self._statistics.mean

    def get_statistics(self):
        return self._statistics

    def get_total_unit(self):
        return self._total_unit

    def get_termination_check(self, ui):
        if self._termination_check is None:
            self._termination_check = TerminationCheck(self, ui)
        return self._termination_check

    def is_completed(self, ui):
        """ Check whether the termination condition is satisfied. """
        return self.get_termination_check(ui).should_terminate(
            self.get_number_of_data_points(), None)

    def run_failed(self):
        return (self._termination_check.fails_consecutively() or
                self._termination_check.has_too_many_failures(
                    self.get_number_of_data_points()))

    def __hash__(self):
        return hash(self.cmdline())

    def as_simple_string(self):
        return "%s %s %s %s" % (self._benchmark.as_simple_string(),
                                self._cores, self._input_size, self._var_value)

    def _expand_vars(self, string):
        try:
            return string % {'benchmark': self._benchmark.command,
                             'cores': self._cores,
                             'executor': self._benchmark.suite.executor.name,
                             'input': self._input_size,
                             'iterations': self.iterations,
                             'suite': self._benchmark.suite.name,
                             'variable': self._var_value,
                             'warmup': self._benchmark.run_details.warmup}
        except ValueError as err:
            self._report_format_issue_and_exit(string, err)
        except TypeError as err:
            self._report_format_issue_and_exit(string, err)
        except KeyError as err:
            msg = ("The configuration of %s contains improper Python format strings.\n"
                   + "{ind}The command line configured is: %s\n"
                   + "{ind}%s is not supported as key.\n"
                   + "{ind}Only benchmark, input, variable, cores, and warmup are supported.\n") % (
                       self._benchmark.name, string, err)
            raise UIError(msg, err)

    def cmdline(self):
        if self._cmdline:
            return self._cmdline
        return self._construct_cmdline()

    def _construct_cmdline(self):
        cmdline = ""
        if self._benchmark.suite.executor.path:
            cmdline = self._benchmark.suite.executor.path + "/"

        cmdline += self._benchmark.suite.executor.executable

        if self._benchmark.suite.executor.args:
            cmdline += " " + str(self._benchmark.suite.executor.args)

        cmdline += " " + self._benchmark.suite.command

        if self._benchmark.extra_args:
            cmdline += " " + str(self._benchmark.extra_args)

        cmdline = self._expand_vars(cmdline)

        self._cmdline = cmdline.strip()
        return self._cmdline

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.cmdline() == other.cmdline())

    def __ne__(self, other):
        return not self.__eq__(other)

    def _report_format_issue_and_exit(self, cmdline, err):
        msg = ("The configuration of the benchmark %s contains an improper Python format string.\n"
               + "{ind}The command line configured is: %s\n"
               + "{ind}Error: %s\n") % (
                   self._benchmark.name, cmdline, err)

        # figure out which format misses a conversion type
        without_conversion_type = re.findall(
            r"%\(.*?\)(?![diouxXeEfFgGcrs%])", cmdline)
        if without_conversion_type:
            msg += ("{ind}The following elements do not have conversion types: \"%s\""
                    + "{ind}This can be fixed by replacing for instance %s with %ss\n") % (
                        '", "'.join(without_conversion_type),
                        without_conversion_type[0], without_conversion_type[0])
        raise UIError(msg, err)

    def as_str_list(self):
        result = self._benchmark.as_str_list()

        result.append(self.cores_as_str)
        result.append(self.input_size_as_str)
        result.append(self.var_value_as_str)

        return result

    def as_dict(self):
        result = dict()
        result['benchmark'] = self._benchmark.as_dict()
        result['cores'] = self._cores
        result['inputSize'] = self._input_size
        result['varValue'] = self._var_value
        result['extraArgs'] = str(self._benchmark.extra_args)
        result['cmdline'] = self.cmdline()
        result['location'] = self.location
        return result

    @classmethod
    def from_str_list(cls, data_store, str_list):
        benchmark = Benchmark.from_str_list(data_store, str_list[:-3])
        return data_store.create_run_id(
            benchmark, str_list[-3], str_list[-2], str_list[-1])

    def __str__(self):
        return "RunId(%s, %s, %s, %s, %s, %d)" % (self._benchmark.name,
                                                  self._cores,
                                                  self._benchmark.extra_args,
                                                  self._input_size or '',
                                                  self._var_value  or '',
                                                  self._benchmark.run_details.warmup or 0)
