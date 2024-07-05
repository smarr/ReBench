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

from .build_cmd import BuildCommand
from .exp_run_details import ExpRunDetails
from .exp_variables import ExpVariables


class BenchmarkSuite(object):

    @classmethod
    def compile(cls, suite_name, suite, executor, build_commands):
        gauge_adapter = suite.get('gauge_adapter')
        command = suite.get('command')

        location = suite.get('location', executor.path)
        if location and not location.startswith('~'):
            location = os.path.abspath(location)
        build = BuildCommand.create_commands(suite.get('build'), build_commands, location)
        benchmarks_config = suite.get('benchmarks')

        description = suite.get('description')
        desc = suite.get('desc')

        run_details = ExpRunDetails.compile(suite, executor.run_details)
        variables = ExpVariables.compile(suite, executor.variables)

        return BenchmarkSuite(suite_name, executor, gauge_adapter, command, location,
                              build, benchmarks_config, description or desc, run_details, variables)

    def __init__(self, suite_name, executor, gauge_adapter, command, location, build,
                 benchmarks_config, desc, run_details, variables):
        """Specialize the benchmark suite for the given executor"""
        self.name = suite_name
        self.executor = executor
        self.gauge_adapter = gauge_adapter
        self.command = command
        self.location = location
        self.build = build

        # This is the raw configuration, i.e., the list of benchmarks and their properties.
        self.benchmarks_config = benchmarks_config

        self._desc = desc
        self.run_details = run_details
        self.variables = variables

    def __str__(self):
        return "Suite(%s, %s)" % (self.name, self.command)

    def as_dict(self):
        result = {
            'name': self.name,
            'executor': self.executor.as_dict(),
            'desc': self._desc
        }
        if self.build:
            result['build'] = [b.as_dict() for b in self.build]
        return result
