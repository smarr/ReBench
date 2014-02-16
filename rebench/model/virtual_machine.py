from rebench.model import value_or_list_as_list

class VirtualMachine(object):
    
    def __init__(self, name, vm_details, global_cfg, _benchmarks, _input_sizes, experiment_name):
        """Specializing the VM details in the run definitions with the settings from
           the VM definitions
        """
        if vm_details:
            benchmarks  = value_or_list_as_list(vm_details.get('benchmark',   _benchmarks)) 
            input_sizes = value_or_list_as_list(vm_details.get('input_sizes', _input_sizes))  
            cores       = value_or_list_as_list(vm_details.get('cores',       None))  
        else:
            benchmarks  = _benchmarks
            input_sizes = _input_sizes
            cores       = None
        
        self._name             = name
        self._benchsuite_names = benchmarks
        self._input_sizes      = input_sizes
            
        self._cores = cores or global_cfg.get('cores', [1])
        
        self._path             = global_cfg['path']
        self._binary           = global_cfg['binary']
        self._args             = global_cfg.get('args', '')
        self._experiment_name  = experiment_name
    
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
