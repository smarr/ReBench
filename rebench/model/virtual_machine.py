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

from . import value_or_list_as_list


class VirtualMachine(object):
    
    def __init__(self, name, vm_details, global_cfg, _benchmarks, _input_sizes,
                 experiment_name):
        """Specializing the VM details in the run definitions with the settings from
           the VM definitions
        """
        if vm_details:
            benchmarks  = value_or_list_as_list(vm_details.get('benchmark',
                                                               _benchmarks))
            input_sizes = value_or_list_as_list(vm_details.get('input_sizes',
                                                               _input_sizes))
            cores       = value_or_list_as_list(vm_details.get('cores',
                                                               None))
        else:
            benchmarks  = _benchmarks
            input_sizes = _input_sizes
            cores       = None
        
        self._name             = name
        self._benchsuite_names = benchmarks
        self._input_sizes      = input_sizes
            
        self._cores = cores or global_cfg.get('cores', [1])
        
        self._path             = os.path.abspath(global_cfg['path'])
        self._binary           = global_cfg['binary']
        self._args             = global_cfg.get('args', '')
        self._experiment_name  = experiment_name
        self._execute_exclusively = global_cfg.get('execute_exclusively', True)
    
    @property
    def name(self):
        return self._name
    
    @property
    def benchmark_suite_names(self):
        return self._benchsuite_names
    
    @property
    def input_sizes(self):
        return self._input_sizes
    
    @property
    def cores(self):
        return self._cores
    
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
    def execute_exclusively(self):
        return self._execute_exclusively
