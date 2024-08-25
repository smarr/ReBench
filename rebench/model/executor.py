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
import subprocess

from .build_cmd import BuildCommand
from .exp_run_details import ExpRunDetails
from .exp_variables import ExpVariables
from .profiler import Profiler
from ..configuration_error import ConfigurationError


class Executor:
    @classmethod
    def compile(cls, executor_name, executor, run_details, variables, build_commands, action):
        path = executor.get('path')
        if path and not path.startswith('~'):
            path = os.path.abspath(path)
        executable = executor.get('executable')
        args = executor.get('args')
        version_command = executor.get('version_command')
        version_string = executor.get('version_string')
        version_git = executor.get('version_git')

        build = BuildCommand.create_commands(executor.get('build'), build_commands, path)
        description = executor.get('description')
        desc = executor.get('desc')
        env = executor.get('env')
        profiler = Profiler.compile(executor.get('profiler'))
        run_details = ExpRunDetails.compile(executor, run_details)
        variables = ExpVariables.compile(executor, variables)

        if action == "profile" and len(profiler) == 0:
            raise ConfigurationError(f"Executor {executor_name} is configured for profiling, "
                                     "but no profiler details are given.")

        return Executor(executor_name, path, executable, args,
                        version_command, version_string, version_git, build,
                        description or desc, profiler, run_details, variables, action, env)

    def __init__(self, name, path, executable, args,
                 version_command, version_string, version_git, build, description,
                 profiler, run_details, variables, action, env):
        """Specializing the executor details in the run definitions with the settings from
                   the executor definitions
        """
        self.name = name
        self.path = path
        self.executable = executable
        self.args = args
        self.version_command = version_command
        self.version_string = version_string
        self.version_git = version_git
        self.build = build
        self.description = description
        self.profiler = profiler
        self.run_details = run_details
        self.variables = variables
        self.env = env
        self.action = action

    def get_version(self):
        if self.version_command:
            try:
                result = subprocess.run(self.version_command, shell=True,
                                        check=True, capture_output=True, text=True)
                return result.stdout.strip()
            except subprocess.CalledProcessError as e:
                return e.stderr.strip()
        elif self.version_string:
            return self.version_string
        elif self.version_git:
            try:
                result = subprocess.run(self.version_git, shell=True,
                                        check=True, capture_output=True, text=True)
                return result.stdout.strip()
            except subprocess.CalledProcessError as e:
                return e.stderr.strip()
        else:
            return None

    def as_dict(self):
        result = {'name': self.name, 'desc': self.description}
        if self.build:
            result['build'] = [b.as_dict() for b in self.build]
        return result
