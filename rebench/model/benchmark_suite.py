from rebench.model import value_or_list_as_list


class BenchmarkSuite(object):

    def __init__(self, suite_name, vm, global_suite_cfg):
        """Specialize the benchmark suite for the given VM"""
        
        self._name = suite_name
        
        ## TODO: why do we do handle input_sizes the other way around?
        if vm.input_sizes:
            self._input_sizes = vm.input_sizes
        else:
            self._input_sizes = global_suite_cfg.get('input_sizes')
        if self._input_sizes is None:
            self._input_sizes = [None]
        
        self._location        = global_suite_cfg.get('location', vm.path)
        self._cores           = global_suite_cfg.get('cores',    vm.cores)
        self._variable_values = value_or_list_as_list(global_suite_cfg.get(
                                                'variable_values', [None]))

        self._vm                 = vm
        self._benchmarks         = value_or_list_as_list(
                                                global_suite_cfg['benchmarks'])
        self._performance_reader = global_suite_cfg['performance_reader']
        self._command            = global_suite_cfg['command']
        self._max_runtime        = global_suite_cfg.get('max_runtime', -1)

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
    def variable_values(self):
        return self._variable_values
    
    @property
    def vm(self):
        return self._vm
    
    @property
    def benchmarks(self):
        return self._benchmarks
    
    @property
    def performance_reader(self):
        return self._performance_reader

    @property
    def name(self):
        return self._name
    
    @property
    def command(self):
        return self._command

    @property
    def max_runtime(self):
        return self._max_runtime
