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
from . import value_with_optional_details
from .exp_run_details import ExpRunDetails
from .exp_variables import ExpVariables


class Benchmark(object):

    @classmethod
    def compile(cls, bench, suite, data_store):
        """Specialization of the configurations which get executed by using the
           suite definitions.
        """
        name, details = value_with_optional_details(bench, {})

        command = details.get('command', name)

        gauge_adapter = details.get('gauge_adapter',
                                    suite.gauge_adapter)
        extra_args = details.get('extra_args', None)
        codespeed_name = details.get('codespeed_name', None)

        run_details = ExpRunDetails.compile(details, suite.run_details)
        run_details.resolve_override_and_important()
        variables = ExpVariables.compile(details, suite.variables)

        return Benchmark(name, command, gauge_adapter, suite,
                         variables, extra_args, run_details, codespeed_name,
                         data_store)

    def __init__(self, name, command, gauge_adapter, suite, variables, extra_args,
                 run_details, codespeed_name, data_store):
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

        # the compiled runs, these might be shared with other benchmarks/suites
        self._runs = set()

        data_store.register_config(self)

    def add_run(self, run):
        self._runs.add(run)

    @property
    def execute_exclusively(self):
        return self.run_details.execute_exclusively

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
        return {
            'name': self.name,
            'runDetails': self.run_details.as_dict(),
            'suite': self.suite.as_dict()
        }

    @classmethod
    def from_str_list(cls, data_store, str_list):
        return data_store.get_config(str_list[0], str_list[1], str_list[2],
                                     None if str_list[3] == '' else str_list[3])
    @classmethod
    def get_column_headers(cls):
        return ["benchmark", "executor", "suite", "extraArgs"]
