class BenchmarkConfig:
    _registry = {}
    
    @classmethod
    def reset(cls):
        cls._registry = {}
    
    @classmethod
    def get_config(cls, name, suiteName, vmName, extra_args = None):
        tmp = BenchmarkConfig(name, None, {'name':suiteName}, {'name':vmName}, extra_args)
        if tmp not in cls._registry:
            raise ValueError("Requested configuration is not available: " + (name, suiteName, vmName, extra_args).__str__())
        
        return cls._registry[tmp]
    
    @classmethod
    def create(cls, bench_def, actions):
        cfg = BenchmarkConfig(**bench_def)
        if cfg in BenchmarkConfig._registry:
            cfg = BenchmarkConfig._registry[cfg]
        else:
            BenchmarkConfig._registry[cfg] = cfg
        
        cfg.set_actions(actions)
        return cfg
    
    def __init__(self, name, performance_reader, suite, vm, extra_args = None, **kwargs):
        self._name = name
        self._extra_args = str(extra_args) if extra_args else None
        self._performance_reader = performance_reader
        self._suite = suite
        self._vm = vm
        self._actions = None
        self._additional_config = kwargs
    
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
    
    @property
    def additional_config(self):
        return self._additional_config
        
    def __str__(self):
        return "%s, vm:%s, suite:%s, args:'%s'" % (self._name,
                                                   self._vm['name'],
                                                   self._suite['name'],
                                                   self._extra_args or '')
    
    def as_simple_string(self):
        if self._extra_args:
            return "%s (%s, %s, %s)"  % (self._name,
                                         self._vm['name'],
                                         self._suite['name'],
                                         self._extra_args)
        else:
            return "%s (%s, %s)"  % (self._name, self._vm['name'], self._suite['name'])
        
    def __eq__(self, other):
        """I am not exactly sure whether that will be right, or whether
           I actually need to take the whole suite and vm dictionaries
           into account"""
        if type(other) != type(self):
            return False
        
        return (    self._name           == other.name
                and self._extra_args     == other.extra_args
                and 0 == cmp(self._suite, other.suite)
                and 0 == cmp(self._vm,    other.vm))
                
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __hash__(self):
        return (hash(self._name) ^ 
                hash(self._extra_args) ^ 
                hash(self._suite['name']) ^
                hash(self._vm['name']))
    
    def as_tuple(self):
        return (self._name, self._vm['name'], self._suite['name'], self._extra_args)
    
    def set_actions(self, actions):
        if self._actions and 0 != cmp(self._actions, actions):
            raise ValueError("Currently the actions for each BenchmarkConfigurations need to be equal.")
        
        self._actions = actions
        return self
    
    def actions(self):
        return self._actions
        
    @classmethod
    def tuple_mapping(cls):
        return {'bench' : 0, 'vm' : 1, 'suite' : 2, 'extra_args' : 3}
