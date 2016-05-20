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
from .virtual_machine  import VirtualMachine
from .benchmark_suite  import BenchmarkSuite
from .benchmark_config import BenchmarkConfig
from .reporting        import Reporting
from . import value_or_list_as_list, value_with_optional_details


class Experiment:
    
    def __init__(self, name, exp_def, global_runs_cfg, global_vms_cfg,
                 global_suite_cfg, global_reporting_cfg, data_store,
                 standard_data_file, discard_old_data, options = None):
        self._name           = name
        self._raw_definition = exp_def
        self._runs_cfg       = global_runs_cfg.combined(exp_def)
        self._reporting      = Reporting(
            global_reporting_cfg,
            options).combined(exp_def.get('reporting', {}))
        self._data_store     = data_store
        self._persistence    = data_store.get(exp_def.get('data_file',
                                                          standard_data_file),
                                              discard_old_data)

        self._vms            = self._compile_virtual_machines(global_vms_cfg)
        self._suites         = self._compile_benchmark_suites(global_suite_cfg)
        self._benchmarks     = self._compile_benchmarks()
        self._runs           = self._compile_runs()

    @property
    def name(self):
        return self._name
    
    def get_runs(self):
        return self._runs
    
    def _compile_runs(self):
        runs = set()
        
        for bench in self._benchmarks:
            for cores in bench.suite.cores:
                for input_size in bench.suite.input_sizes:
                    for var_val in bench.suite.variable_values:
                        run = self._data_store.create_run_id(
                            bench, cores, input_size, var_val)
                        bench.add_run(run)
                        runs.add(run)
                        run.add_reporting(self._reporting)
                        run.add_persistence(self._persistence)
                        run.set_run_config(self._runs_cfg)
        return runs
    
    def _compile_virtual_machines(self, global_vms_cfg):
        benchmarks  = value_or_list_as_list(self._raw_definition.
                                            get( 'benchmark', None))
        input_sizes = value_or_list_as_list(self._raw_definition.
                                            get('input_sizes', None))
        executions  = value_or_list_as_list(self._raw_definition['executions'])
        
        vms = []
        
        for vm in executions:
            vm, vm_details = value_with_optional_details(vm)
            if vm not in global_vms_cfg:
                raise ValueError("The VM '%s' requested in %s was not found."
                                 % (vm, self.name))
            
            global_cfg = global_vms_cfg[vm]
            vms.append(VirtualMachine(vm, vm_details, global_cfg, benchmarks,
                                      input_sizes, self.name))
        return vms
    
    def _compile_benchmark_suites(self, global_suite_cfg):
        suites = []
        for vm in self._vms:
            for suite_name in vm.benchmark_suite_names:
                suites.append(BenchmarkSuite(suite_name, vm,
                                             global_suite_cfg[suite_name]))
        return suites
    
    def _compile_benchmarks(self):
        bench_cfgs = []
        for suite in self._suites:
            for bench in value_or_list_as_list(suite.benchmarks):
                bench_cfgs.append(BenchmarkConfig.compile(
                    bench, suite, self._data_store))
        return bench_cfgs
