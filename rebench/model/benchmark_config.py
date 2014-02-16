from rebench.model import value_with_optional_details


class BenchmarkConfig(object):
    _registry = {}
    
    @classmethod
    def reset(cls):
        cls._registry = {}
    
    @classmethod
    def get_config(cls, name, vm_name, suite_name, extra_args):
        key = (name, vm_name, suite_name,
               '' if extra_args is None else str(extra_args))

        if key not in BenchmarkConfig._registry:
            raise ValueError("Requested configuration is not available: " +
                             key.__str__())

        return BenchmarkConfig._registry[key]
    
    @classmethod
    def compile(cls, bench, suite):
        """Specialization of the configurations which get executed by using the
           suite definitions.
        """
        name, details = value_with_optional_details(bench, {})
        
        performance_reader = details.get('performance_reader',
                                         suite.performance_reader)
        extra_args         = details.get('extra_args', None)
        return BenchmarkConfig(name, performance_reader, suite, suite.vm,
                               extra_args)

    @classmethod
    def _register(cls, cfg):
        key = tuple(cfg.as_str_list())
        if key in BenchmarkConfig._registry:
            raise ValueError("Two identical BenchmarkConfig tried to register. "
                             + "This seems to be wrong.")
        else:
            BenchmarkConfig._registry[key] = cfg
        return cfg
    
    def __init__(self, name, performance_reader, suite, vm, extra_args = None):
        self._name               = name
        self._extra_args         = extra_args
        self._performance_reader = performance_reader
        self._suite = suite
        self._vm = vm
        self._runs = set()      # the compiled runs, these might be shared
                                # with other benchmarks/suites
        self._register(self)
    
    def add_run(self, run):
        self._runs.add(run)
    
    @property
    def name(self):
        return self._name
    
    @property
    def extra_args(self):
        return self._extra_args
    
    @property
    def performance_reader(self):
        return self._performance_reader
    
    @property
    def suite(self):
        return self._suite
    
    @property
    def vm(self):
        return self._vm
    
    def __str__(self):
        return "%s, vm:%s, suite:%s, args:'%s'" % (self._name,
                                                   self._vm.name,
                                                   self._suite.name,
                                                   self._extra_args or '')
    
    def as_simple_string(self):
        if self._extra_args:
            return "%s (%s, %s, %s)"  % (self._name,
                                         self._vm.name,
                                         self._suite.name,
                                         self._extra_args)
        else:
            return "%s (%s, %s)" % (self._name, self._vm.name, self._suite.name)
        
    def as_str_list(self):
        return [self._name, self._vm.name, self._suite.name,
                '' if self._extra_args is None else str(self._extra_args)]

    @classmethod
    def from_str_list(cls, str_list):
        return cls.get_config(str_list[0], str_list[1], str_list[2],
                              None if str_list[3] == '' else str_list[3])