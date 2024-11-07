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

from typing import Optional, Mapping

from .build_cmd import BuildCommand
from .exp_run_details import ExpRunDetails
from .exp_variables import ExpVariables
from .profiler import Profiler
from ..configuration_error import ConfigurationError


class Executor(object):

    @classmethod
    def compile(cls, executor_name, executor, run_details,
                variables, deduplicated_build_commands, action):
        path = executor.get("path")
        if path and not path.startswith("~"):
            path = os.path.abspath(path)
        executable = executor.get("executable")
        args = executor.get("args")

        build = BuildCommand.create(executor.get("build"), path, deduplicated_build_commands)

        description = executor.get("description")
        desc = executor.get("desc")
        env = executor.get("env")

        profiler = Profiler.compile(executor.get("profiler"))

        run_details = ExpRunDetails.compile(executor, run_details)
        variables = ExpVariables.compile(executor, variables)

        if action == "profile" and len(profiler) == 0:
            raise ConfigurationError("Executor " + executor_name + " is configured for profiling, "
                                     + "but no profiler details are given.")

        return Executor(executor_name, path, executable, args, build, description or desc,
                        profiler, run_details, variables, action, env)

    def __init__(self, name, path, executable, args, build: Optional[BuildCommand], description,
                 profiler: Optional[list[Profiler]], run_details: ExpRunDetails,
                 variables: ExpVariables, action, env):
        """Specializing the executor details in the run definitions with the settings from
           the executor definitions
        """
        self.name = name
        self.path = path
        self.executable = executable
        self.args = args

        self.build = build
        self.description = description
        self.profiler = profiler

        self.run_details = run_details
        self.variables = variables
        self.env = env

        self.action = action

    def __eq__(self, other) -> bool:
        return self is other or (
            self.name == other.name and
            self.description == other.description and
            self.action == other.action and
            self.path == other.path and
            self.executable == other.executable and
            self.args == other.args and
            self.build == other.build and
            self.run_details == other.run_details and
            self.variables == other.variables)

    # pylint: disable-next=too-many-return-statements
    def __lt__(self, other) -> bool:
        if self is other:
            return False

        if self.name != other.name:
            return self.name < other.name

        if self.description != other.description:
            return self.description < other.description

        if self.action != other.action:
            return self.action < other.action

        if self.path != other.path:
            return self.path < other.path

        if self.executable != other.executable:
            return self.executable < other.executable

        if self.args != other.args:
            return self.args < other.args

        if self.build != other.build:
            return self.build < other.build

        if self.run_details != other.run_details:
            return self.run_details < other.run_details

        return self.variables < other.variables

    def __hash__(self):
        return hash((self.name, self.description, self.action, self.path, self.executable,
                     self.args, self.build, self.run_details, self.variables))

    def as_dict(self):
        result = {
            'name': self.name,
            'executable': self.executable,
            'action': self.action,
            'runDetails': self.run_details.as_dict(),
            'variables': self.variables.as_dict(),
        }
        if self.path is not None:
            result['path'] = self.path
        if self.args is not None:
            result['args'] = self.args
        if self.description is not None:
            result['desc'] = self.description
        if self.build is not None:
            result["build"] = self.build.as_dict()
        return result

    @classmethod
    def from_dict(cls, data: Mapping) -> "Executor":
        path = data.get("path", None)
        build = BuildCommand.from_dict(data.get("build", None), path)
        return Executor(data["name"], path, data["executable"],
                        data.get("args", None), build, data.get("desc", None),
                        Profiler.from_dict(data.get("profiler", None)),
                        ExpRunDetails.from_dict(data.get("runDetails", None)),
                        ExpVariables.from_dict(data.get("variables", None)),
                        data.get("action", None),
                        data.get("env", None))
