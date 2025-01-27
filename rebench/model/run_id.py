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
import os
import re
import shlex
from typing import TYPE_CHECKING, Any

from typing import Optional, Mapping, Union

from .benchmark import Benchmark
from .termination_check import TerminationCheck
from ..output import UIError
from ..statistics import StatisticProperties, SampleCounter

if TYPE_CHECKING:
    from ..persistence import AbstractPersistence
    from ..reporter import Reporter
    from ..statistics import WithSamples


def expand_user(possible_path, shell_escape):
    something_changed = False

    # split will change the type of quotes, which may cause issues with shell variables
    parts = shlex.split(possible_path)
    for i, part in enumerate(parts):
        expanded = os.path.expanduser(part)
        if "~" in expanded and ":" in expanded:
            path_list = expanded.split(":")
            expanded = ":".join([os.path.expanduser(p) for p in path_list])
        if parts[i] != expanded:
            something_changed = True
            parts[i] = expanded

    if something_changed:
        if shell_escape:
            return shlex.join(parts)
        return ' '.join(parts)

    return possible_path


class RunId(object):
    """
    A RunId is a concrete instantiation of the possible combinations of
    configurations defined by the `Benchmark` instance.
    """

    def __init__(self, benchmark: Benchmark, cores: Optional[Union[str, int]],
                 input_size: Optional[str], var_value: Optional[str],
                 tag: Optional[str], machine: Optional[str]):
        self.benchmark = benchmark
        self.cores = cores
        self.input_size = input_size
        self.var_value = var_value
        self.tag = tag
        self.machine = machine

        self._reporters: set[Reporter] = set()
        self._persistence: set[AbstractPersistence] = set()

        self.statistics: WithSamples

        if self.is_profiling():
            self.statistics = SampleCounter()
        else:
            self.statistics = StatisticProperties()
        self.total_unit = None

        self._termination_check = None
        self._cmdline = None
        self.executable = None
        self.executable_missing = False
        self.is_failed = True

        self._max_invocation = 0
        self._expandend_env = None

        self._hash = None

    def has_same_executable(self, other):
        return self.executable == other.executable

    @property
    def warmup_iterations(self):
        return self.benchmark.run_details.warmup

    @property
    def min_iteration_time(self):
        return self.benchmark.run_details.min_iteration_time

    @property
    def max_invocation_time(self):
        return self.benchmark.run_details.max_invocation_time

    @property
    def ignore_timeouts(self):
        return self.benchmark.run_details.ignore_timeouts

    @property
    def retries_after_failure(self):
        return self.benchmark.run_details.retries_after_failure

    @property
    def iterations(self):
        return self.benchmark.run_details.iterations

    @property
    def invocations(self):
        return self.benchmark.run_details.invocations

    @property
    def env(self):
        if self._expandend_env is not None:
            return self._expandend_env

        self._expandend_env = self.benchmark.run_details.env
        for key, value in self._expandend_env.items():
            self._expandend_env[key] = expand_user(value, False)
        return self._expandend_env

    @property
    def completed_invocations(self):
        return self._max_invocation

    @property
    def execute_exclusively(self):
        return self.benchmark.run_details.execute_exclusively

    @property
    def cores_as_str(self):
        return "" if self.cores is None else str(self.cores)

    @property
    def input_size_as_str(self):
        return "" if self.input_size is None else str(self.input_size)

    @property
    def var_value_as_str(self):
        return "" if self.var_value is None else str(self.var_value)

    @property
    def tag_as_str(self):
        return "" if self.tag is None else str(self.tag)

    @property
    def machine_as_str(self):
        return '' if self.machine is None else self.machine

    @property
    def location(self):
        if not self.benchmark.suite.location:
            return None
        return self._expand_vars(self.benchmark.suite.location)

    def get_gauge_adapter(self):
        if self.is_profiling():
            # TODO: needs changing once we want to support different profilers
            perf_profile = self.benchmark.suite.executor.profiler[0]
            return perf_profile.gauge_adapter_name
        return self.benchmark.gauge_adapter

    def get_gauge_adapter_name(self):
        if self.is_profiling():
            return self.get_gauge_adapter()

        adapter = self.benchmark.gauge_adapter
        if isinstance(adapter, str):
            return adapter
        return next(iter(adapter))  # get the first key in the dict

    def is_profiling(self) -> bool:
        return self.benchmark.suite.executor.action == "profile"

    def build_commands(self):
        commands = set()
        builds = self.benchmark.suite.executor.build
        if builds:
            commands.add(builds)
        builds = self.benchmark.suite.build
        if builds:
            commands.add(builds)
        return commands

    def requires_warmup(self):
        return self.benchmark.run_details.warmup > 0

    def fail_immediately(self):
        self._termination_check.fail_immediately()

    def indicate_failed_execution(self):
        self._termination_check.indicate_failed_execution()

    def indicate_successful_execution(self):
        self.is_failed = False
        self._termination_check.indicate_successful_execution()

    def add_reporter(self, reporter):
        self._reporters.add(reporter)

    def add_reporting(self, reporting):
        self._reporters.update(reporting.get_reporters())

    def report_run_failed(self, cmdline, return_code, output):
        for reporter in self._reporters:
            reporter.run_failed(self, cmdline, return_code, output)

    def report_run_completed(self, cmdline):
        for reporter in self._reporters:
            reporter.run_completed(self, self.statistics, cmdline)
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
        if self.total_unit is None:
            self.total_unit = data_point.get_total_unit()
        if not warmup:
            self.statistics.add_sample(data_point.get_total_value())

    def loaded_data_point(self, data_point, warmup):
        for persistence in self._persistence:
            persistence.loaded_data_point(data_point)
        self._new_data_point(data_point, warmup)

    def add_data_point(self, data_point, warmup):
        self._new_data_point(data_point, warmup)

        for persistence in self._persistence:
            persistence.persist_data_point(data_point)

    def get_number_of_data_points(self):
        return self.statistics.num_samples

    def get_mean_of_totals(self):
        return self.statistics.mean

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
        if self._hash is None:
            self._hash = hash((self.benchmark, self.cores, self.input_size, self.var_value,
                               self.tag, self.machine))
        return self._hash

    def as_simple_string(self):
        return "%s %s %s %s %s" % (
            self.benchmark.as_simple_string(),
            self.cores, self.input_size, self.var_value, self.tag)

    def _expand_vars(self, string):
        try:
            return string % {'benchmark': self.benchmark.command,
                             'cores': self.cores_as_str,
                             'executor': self.benchmark.suite.executor.name,
                             'input': self.input_size_as_str,
                             'iterations': self.iterations,

                             # the invocation number needs to be set right before execution
                             # we don't know it here, and it would change the RunId identity
                             'invocation': '%(invocation)s',
                             'suite': self.benchmark.suite.name,
                             'variable': self.var_value_as_str,
                             'tag': self.tag_as_str,
                             'warmup': self.benchmark.run_details.warmup}
        except ValueError as err:
            self._report_format_issue_and_exit(string, err)
            return None
        except TypeError as err:
            self._report_format_issue_and_exit(string, err)
            return None
        except KeyError as err:
            msg = ("The configuration of %s contains improper Python format strings.\n"
                   + "{ind}The command line configured is: %s\n"
                   + "{ind}%s is not supported as key.\n"
                   + "{ind}Only benchmark, input, variable, cores, and warmup are supported.\n") % (
                       self.benchmark.name, string, err)
            raise UIError(msg, err)

    def cmdline(self):
        if self._cmdline:
            return self._cmdline
        return self._construct_cmdline()

    def cmdline_for_next_invocation(self):
        """Replace the invocation number in the command line"""
        cmdline = self.cmdline() % {"invocation": self.completed_invocations + 1}
        cmdline = expand_user(cmdline, True)
        return cmdline

    def _construct_cmdline(self):
        cmdline = ""
        if self.benchmark.suite.executor.path:
            cmdline = self.benchmark.suite.executor.path + "/"

        cmdline += self.benchmark.suite.executor.executable

        if self.benchmark.suite.executor.args:
            cmdline += " " + str(self.benchmark.suite.executor.args)

        cmdline += " " + self.benchmark.suite.command

        if self.benchmark.extra_args:
            cmdline += " " + str(self.benchmark.extra_args)

        cmdline = self._expand_vars(cmdline)

        self._cmdline = cmdline.strip()
        self.executable = cmdline.split(" ")[0]
        return self._cmdline

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return (
            self.cores == other.cores and
            self.input_size == other.input_size and
            self.var_value == other.var_value and
            self.tag == other.tag and
            self.benchmark == other.benchmark and
            self.machine == other.machine)

    def __ne__(self, other):
        return not self.__eq__(other)

    # pylint: disable=too-many-return-statements
    def __lt__(self, other):
        if not isinstance(other, self.__class__):
            return False

        if self is other:
            return False

        if self.benchmark != other.benchmark:
            return self.benchmark < other.benchmark

        if self.cores != other.cores:
            return self.cores < other.cores

        if self.input_size != other.input_size:
            return self.input_size < other.input_size

        if self.var_value != other.var_value:
            return self.var_value < other.var_value

        if self.tag != other.tag:
            return self.tag < other.tag

        return self.machine < other.machine

    def _report_format_issue_and_exit(self, cmdline, err):
        msg = ("The configuration of the benchmark %s contains an improper Python format string.\n"
               + "{ind}The command line configured is: %s\n"
               + "{ind}Error: %s\n") % (
                   self.benchmark.name, cmdline, err)

        # figure out which format misses a conversion type
        without_conversion_type = re.findall(
            r"%\(.*?\)(?![diouxXeEfFgGcrs%])", cmdline)
        if without_conversion_type:
            msg += ("{ind}The following elements do not have conversion types: \"%s\""
                    + "{ind}This can be fixed by replacing for instance %s with %ss\n") % (
                        '", "'.join(without_conversion_type),
                        without_conversion_type[0], without_conversion_type[0])
        raise UIError(msg, err)

    def as_str_list(self, persisted_run_id: int):
        result = self.benchmark.as_str_list()

        result.append(self.cores_as_str)
        result.append(self.input_size_as_str)
        result.append(self.var_value_as_str)
        result.append(self.tag_as_str)
        result.append(self.machine_as_str)
        result.append(str(persisted_run_id))

        return result

    def as_dict(self, without_benchmark = False):
        extra_args = self.benchmark.extra_args
        result = {
            'cmdline': self.cmdline()
        }

        location = self.location
        if location is not None:
            result['location'] = location

        if not without_benchmark:
            result['benchmark'] = self.benchmark.as_dict()

        if self.cores is not None:
            result['cores'] = self.cores
        if self.input_size is not None:
            result['inputSize'] = self.input_size
        if self.var_value is not None:
            result['varValue'] = self.var_value
        if self.tag is not None:
            result['tag'] = self.tag
        if extra_args is not None:
            result['extraArgs'] = str(extra_args)
        if self.machine is not None:
            result["machine"] = self.machine

        return result

    @classmethod
    def from_dict(cls, data: Mapping[str, Any], benchmark = False) -> "RunId":
        if not benchmark:
            benchmark = Benchmark.from_dict(data['benchmark'])
        run_id = RunId(benchmark, data.get('cores', None), data.get('inputSize', None),
                       data.get('varValue', None),
                       data.get('tag', None), data.get("machine", None))

        run_id._cmdline = data['cmdline']
        return run_id

    @classmethod
    def from_str_list(cls, id_to_run_id: list["RunId"], str_list):
        run_id_id = int(str_list[-1])
        if run_id_id < len(id_to_run_id):
            return id_to_run_id[run_id_id]
        else:
            raise UIError("Possibly corrupted data file. run_id %d not found." % run_id_id, None)

    @classmethod
    def get_column_headers(cls):
        benchmark_headers = Benchmark.get_column_headers()
        return benchmark_headers + ["cores", "inputSize", "varValue", "tag", "machine", "runId"]

    def __str__(self):
        return "RunId(%s, %s, %s, %s, %s, %s, %s, %d)" % (
            self.benchmark.name,
            self.cores,
            self.benchmark.extra_args,
            self.input_size or '',
            self.var_value  or '',
            self.tag or '',
            self.machine or '',
            self.benchmark.run_details.warmup or 0)
