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


class Executor(object):

    @classmethod
    def compile(cls, executor_name, executor, run_details, variables, build_commands):
        path = executor.get('path')
        if path:
            path = os.path.abspath(path)
        executable = executor.get('executable')
        args = executor.get('args')

        build = BuildCommand.create_commands(executor.get('build'), build_commands, path)

        description = executor.get('description')
        desc = executor.get('desc')

        run_details = ExpRunDetails.compile(executor, run_details)
        variables = ExpVariables.compile(executor, variables)

        return Executor(executor_name, path, executable, args, build, description or desc,
                        run_details, variables)

    def __init__(self, name, path, executable, args, build, description,
                 run_details, variables):
        """Specializing the executor details in the run definitions with the settings from
           the executor definitions
        """
        self._name = name

        self._path = path
        self._executable = executable
        self._args = args

        self._build = build
        self._description = description

        self._run_details = run_details
        self._variables = variables

    @property
    def name(self):
        return self._name

    @property
    def path(self):
        return self._path

    @property
    def executable(self):
        return self._executable

    @property
    def args(self):
        return self._args

    @property
    def build(self):
        return self._build

    @property
    def description(self):
        return self._description

    @property
    def run_details(self):
        return self._run_details

    @property
    def variables(self):
        return self._variables

    def as_dict(self):
        result = dict()
        result['name'] = self._name
        if self._build:
            result['build'] = [b.as_dict() for b in self._build]
        result['desc'] = self._description
        return result
