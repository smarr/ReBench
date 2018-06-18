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
from .build_cmd import BuildCommand
from .exp_run_details import ExpRunDetails
from .exp_variables import ExpVariables


class BenchmarkSuite(object):

    @classmethod
    def compile(cls, suite_name, suite, vm, run_details, variables, build_commands):
        gauge_adapter = suite.get('gauge_adapter')
        command = suite.get('command')

        # TODO: should the location be made absolute as the vm._path??
        location = suite.get('location', vm.path)
        build = BuildCommand.create(suite.get('build'), build_commands, location)
        benchmarks_config = suite.get('benchmarks')

        description = suite.get('description')
        desc = suite.get('desc')

        run_details = ExpRunDetails.compile(suite, run_details)
        variables = ExpVariables.compile(suite, variables)

        return BenchmarkSuite(suite_name, vm, gauge_adapter, command, location,
                              build, benchmarks_config, description or desc, run_details, variables)

    def __init__(self, suite_name, vm, gauge_adapter, command, location, build,
                 benchmarks_config, desc, run_details, variables):
        """Specialize the benchmark suite for the given VM"""
        self._name = suite_name
        self._vm = vm
        self._gauge_adapter = gauge_adapter
        self._command = command
        self._location = location
        self._build = build
        self._benchmarks_config = benchmarks_config
        self._desc = desc
        self._run_details = run_details
        self._variables = variables

    @property
    def variables(self):
        return self._variables

    @property
    def location(self):
        return self._location

    @property
    def run_details(self):
        return self._run_details

    @property
    def build(self):
        return self._build

    @property
    def vm(self):
        return self._vm

    @property
    def benchmarks_config(self):
        """
        This is the raw configuration, i.e.,
        the list of benchmarks and their properties.
        """
        return self._benchmarks_config

    @property
    def gauge_adapter(self):
        return self._gauge_adapter

    @property
    def name(self):
        return self._name

    @property
    def command(self):
        return self._command

    def __str__(self):
        return "Suite(%s, %s)" % (self._name, self._command)
