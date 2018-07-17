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


class VirtualMachine(object):

    @classmethod
    def compile(cls, vm_name, vm, run_details, variables, build_commands):
        path = vm.get('path')
        if path:
            path = os.path.abspath(path)
        binary = vm.get('binary')
        args = vm.get('args')

        build = BuildCommand.create_commands(vm.get('build'), build_commands, path)

        description = vm.get('description')
        desc = vm.get('desc')

        run_details = ExpRunDetails.compile(vm, run_details)
        variables = ExpVariables.compile(vm, variables)

        return VirtualMachine(vm_name, path, binary, args, build, description or desc,
                              run_details, variables)

    def __init__(self, name, path, binary, args, build, description,
                 run_details, variables):
        """Specializing the VM details in the run definitions with the settings from
           the VM definitions
        """
        self._name = name

        self._path = path
        self._binary = binary
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
    def binary(self):
        return self._binary

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
