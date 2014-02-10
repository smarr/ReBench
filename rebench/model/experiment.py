from virtual_machine  import VirtualMachine
from benchmark_suite  import BenchmarkSuite
from benchmark_config import BenchmarkConfig
from reporting        import Reporting 
from run_id           import RunId 
from . import value_or_list_as_list, value_with_optional_details

class Experiment:
    
    def __init__(self, name, exp_def, global_runs_cfg, global_vms_cfg, global_suite_cfg, global_reporting_cfg):
        self._name           = name
        self._raw_definition = exp_def
        self._runs           = global_runs_cfg.combined(exp_def)
        self._reporting      = Reporting(global_reporting_cfg).combined(exp_def.get('reporting', {}))
        
        self._vms            = self._compile_virtual_machines(global_vms_cfg)
        self._suites         = self._compile_benchmark_suites(global_suite_cfg)
        self._benchmarks     = self._compile_benchmarks()
        
        self._runs = None
    
    @property
    def name(self):
        return self._name
    
    def get_runs(self):
        if self._runs is None:
            self._runs = self._compile_runs()
        return self._runs
    
    def _compile_runs(self):
        runs = set()
        
        for bench in self._benchmarks:
            for cores in bench.suite.cores:
                for input_size in bench.suite.input_sizes:
                    for var_val in bench.suite.variable_values:
                        run = RunId.create(bench, (cores, input_size, var_val)) 
                        bench.add_run(run)
                        runs.add(run)
                        run.add_reporting(self._reporting)
        return runs
    
    def _compile_virtual_machines(self, global_vms_cfg):
        benchmarks  = value_or_list_as_list(self._raw_definition.get(  'benchmark', None))
        input_sizes = value_or_list_as_list(self._raw_definition.get('input_sizes', None))
        executions  = value_or_list_as_list(self._raw_definition['executions'])
        
        vms = []
        
        for vm in executions:
            vm, vmDetails = value_with_optional_details(vm)
            if vm not in global_vms_cfg:
                raise ValueError("The VM '%s' requested in %s was not found." % (vm, self.name))
            
            global_cfg = global_vms_cfg[vm]
            vms.append(VirtualMachine(vm, vmDetails, global_cfg, benchmarks,
                                                input_sizes, self.name))
        return vms
    
    def _compile_benchmark_suites(self, global_suite_cfg):
        suites = []
        for vm in self._vms:
            for suite_name in vm.benchmark_suite_names:
                suites.append(BenchmarkSuite(suite_name, vm, global_suite_cfg[suite_name]))
        return suites
    
    def _compile_benchmarks(self):
        bench_cfgs = []
        for suite in self._suites:
            for bench in value_or_list_as_list(suite.benchmarks):
                bench_cfgs.append(BenchmarkConfig.compile(bench, suite))
        return bench_cfgs
    