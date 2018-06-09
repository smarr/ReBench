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


class BenchmarkSuite(object):

    def __init__(self, suite_name, vm, global_suite_cfg, build_commands):
        """Specialize the benchmark suite for the given VM"""

        self._name = suite_name

        ## TODO: why do we do handle input_sizes the other way around?
        if vm.input_sizes:
            self._input_sizes = vm.input_sizes
        else:
            self._input_sizes = global_suite_cfg.get('input_sizes')
        if self._input_sizes is None:
            self._input_sizes = [None]

        # TODO: should the _location be made absolute as the vm._path??
        self._location        = global_suite_cfg.get('location', vm.path)
        self._cores           = global_suite_cfg.get('cores',    vm.cores)
        self._variable_values = global_suite_cfg.get('variable_values', [None])

        self._vm                 = vm
        self._benchmarks         = global_suite_cfg['benchmarks']
        self._gauge_adapter      = global_suite_cfg['gauge_adapter']

        self._command            = global_suite_cfg['command']
        self._max_runtime        = global_suite_cfg.get('max_runtime', -1)

        build = global_suite_cfg.get('build', None)
        if build:
            build_command = BuildCommand(build, self._location)
            if build_command in build_commands:
                build_command = build_commands[build_command]
            self._build = build_command
        else:
            self._build = None

    @property
    def input_sizes(self):
        return self._input_sizes

    @property
    def location(self):
        return self._location

    @property
    def cores(self):
        return self._cores

    @property
    def build(self):
        return self._build

    @property
    def variable_values(self):
        return self._variable_values

    @property
    def vm(self):
        return self._vm

    @property
    def benchmarks(self):
        return self._benchmarks

    @property
    def gauge_adapter(self):
        return self._gauge_adapter

    @property
    def name(self):
        return self._name

    @property
    def command(self):
        return self._command

    @property
    def max_runtime(self):
        return self._max_runtime

    def has_max_runtime(self):
        return self._max_runtime != -1

    def __str__(self):
        return "Suite(%s, %s)" % (self._name, self._command)
