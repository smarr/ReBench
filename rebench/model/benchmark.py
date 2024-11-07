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
from typing import TYPE_CHECKING, Mapping, Any, Optional

from . import value_with_optional_details
from .benchmark_suite import BenchmarkSuite
from .exp_run_details import ExpRunDetails
from .exp_variables import ExpVariables

if TYPE_CHECKING:
    from ..interop.adapter import GaugeAdapter


class Benchmark(object):

    @classmethod
    def compile(cls, bench, suite):
        """Specialization of the configurations which get executed by using the
           suite definitions.
        """
        name, details = value_with_optional_details(bench, {})

        command = details.get("command", name)

        gauge_adapter = details.get('gauge_adapter',
                                    suite.gauge_adapter)
        extra_args = details.get('extra_args', None)
        codespeed_name = details.get('codespeed_name', None)

        run_details = ExpRunDetails.compile(details, suite.run_details)
        run_details.resolve_override_and_important()
        variables = ExpVariables.compile(details, suite.variables)

        return Benchmark(name, command, gauge_adapter, suite,
                         variables, extra_args, run_details, codespeed_name)

    def __init__(self, name: str, command: str, gauge_adapter: Optional["GaugeAdapter"],
                 suite: "BenchmarkSuite", variables: Optional[ExpVariables], extra_args: str,
                 run_details: "ExpRunDetails", codespeed_name: Optional[str]):
        assert run_details is None or isinstance(run_details, ExpRunDetails)
        self.name = name

        """
        We distinguish between the benchmark name, used for reporting, and the
        command that is passed to the benchmark executor.
        If no command was specified in the config, the name is used instead.
        See the compile(.) method for details.

        :return: the command to be passed to the benchmark invocation
        """
        self.command = command

        self.extra_args = extra_args
        self.codespeed_name = codespeed_name
        self.run_details = run_details
        self.gauge_adapter = gauge_adapter
        self.suite = suite

        self.variables = variables
        self._hash = None

    @property
    def execute_exclusively(self):
        return self.run_details.execute_exclusively

    def __eq__(self, other) -> bool:
        return self is other or (
            self.name == other.name and
            self.command == other.command and
            self.extra_args == other.extra_args and
            self.run_details == other.run_details and
            self.variables == other.variables and
            self.suite == other.suite)

    # pylint: disable-next=too-many-return-statements
    def __lt__(self, other) -> bool:
        if self is other:
            return False

        if self.name != other.name:
            return self.name < other.name

        if self.command != other.command:
            return self.command < other.command

        if self.suite != other.suite:
            return self.suite < other.suite

        if self.extra_args != other.extra_args:
            return self.extra_args < other.extra_args

        if self.run_details != other.run_details:
            return self.run_details < other.run_details

        return self.variables < other.variables

    def __hash__(self):
        if self._hash is None:
            self._hash = hash((self.name, self.command, self.extra_args, self.run_details,
                               self.variables, self.suite))
        return self._hash

    def __str__(self):
        return "%s, executor:%s, suite:%s, args:'%s'" % (
            self.name, self.suite.executor.name, self.suite.name, self.extra_args or '')

    def as_simple_string(self):
        if self.extra_args:
            return "%s (%s, %s, %s)"  % (self.name, self.suite.executor.name,
                                         self.suite.name, self.extra_args)
        else:
            return "%s (%s, %s)" % (self.name, self.suite.executor.name, self.suite.name)

    def as_str_list(self):
        return [self.name, self.suite.executor.name, self.suite.name,
                '' if self.extra_args is None else str(self.extra_args)]

    def as_dict(self):
        result = {
            "name": self.name,
            "command": self.command,
            "runDetails": self.run_details.as_dict(),
            "suite": self.suite.as_dict(),
            "variables": self.variables.as_dict()
        }

        if self.extra_args is not None:
            result["extra_args"] = self.extra_args
        return result

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Benchmark":
        run_details = ExpRunDetails.from_dict(data["runDetails"])
        suite = BenchmarkSuite.from_dict(data["suite"])
        variables = ExpVariables.from_dict(data.get("variables", None))

        return Benchmark(data["name"], data["command"], None, suite, variables,
                         data.get("extra_args", None), run_details, None)

    @classmethod
    def get_column_headers(cls):
        return ["benchmark", "executor", "suite", "extraArgs"]
