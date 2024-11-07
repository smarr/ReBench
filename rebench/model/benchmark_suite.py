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
from typing import Mapping, Optional

from .build_cmd import BuildCommand
from .executor import Executor
from .exp_run_details import ExpRunDetails
from .exp_variables import ExpVariables


class BenchmarkSuite(object):

    @classmethod
    def compile(cls, suite_name, suite, executor: Executor, deduplicated_build_commands):
        gauge_adapter = suite.get("gauge_adapter")
        command = suite.get("command")

        location = suite.get("location", executor.path)
        if location and not location.startswith("~"):
            location = os.path.abspath(location)
        build = BuildCommand.create(suite.get("build"), location, deduplicated_build_commands)
        benchmarks_config = suite.get("benchmarks")

        description = suite.get("description")
        desc = suite.get("desc")

        run_details = ExpRunDetails.compile(suite, executor.run_details)
        variables = ExpVariables.compile(suite, executor.variables)

        return BenchmarkSuite(suite_name, executor, gauge_adapter, command, location,
                              build, benchmarks_config, description or desc, run_details, variables)

    def __init__(self, suite_name, executor: "Executor", gauge_adapter, command, location,
                 build: Optional[BuildCommand],
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

    def __eq__(self, other) -> bool:
        return self is other or (
            self.name == other.name and
            self.command == other.command and
            self.location == other.location and
            self._desc == other._desc and
            self.build == other.build and
            self.executor == other.executor)

    # pylint: disable-next=too-many-return-statements
    def __lt__(self, other: "BenchmarkSuite") -> bool:
        if self is other:
            return False

        if self.name != other.name:
            return self.name < other.name

        if self.command != other.command:
            return self.command < other.command

        if self.location != other.location:
            return self.location < other.location

        if self._desc != other._desc:
            return self._desc < other._desc

        if self.build != other.build:
            if self.build is None:
                return True
            return self.build < other.build

        return self.executor < other.executor

    def __hash__(self):
        return hash((self.name, self.command, self.location, self._desc, self.build, self.executor))

    def __str__(self):
        return "Suite(%s, %s)" % (self.name, self.command)

    def as_dict(self):
        result = {
            "name": self.name,
            "command": self.command,
            "executor": self.executor.as_dict(),
        }

        if self.location is not None:
            result["location"] = self.location

        if self._desc is not None:
            result["desc"] = self._desc

        if self.build is not None:
            result["build"] = self.build.as_dict()
        return result

    @classmethod
    def from_dict(cls, data: Mapping) -> "BenchmarkSuite":
        executor = Executor.from_dict(data["executor"])
        location = data.get("location", None)
        build = BuildCommand.from_dict(data.get("build", None), location)

        return BenchmarkSuite(data["name"], executor, None, data["command"],
                              location,
                              build, None, data.get("desc", None), None, None)
