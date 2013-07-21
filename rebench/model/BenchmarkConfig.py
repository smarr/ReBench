class BenchmarkConfig:
    _registry = {}
    
    @classmethod
    def reset(cls):
        cls._registry = {}
    
    @classmethod
    def get_config(cls, name, suiteName, vmName, extra_args = None):
        tmp = BenchmarkConfig(name, None, {'name':suiteName}, {'name':vmName}, extra_args)
        if tmp not in cls._registry:
            raise ValueError("Requested configuration is not available: " + (cls, name, suiteName, vmName, extra_args).__str__())
        
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
    
    def __init__(self, name, performance_reader, suite, vm, extra_args = None):
        self.name = name
        self.extra_args = str(extra_args) if extra_args else None
        self.performance_reader = performance_reader
        self.suite = suite
        self.vm = vm
        self._actions = None
        
    def __str__(self):
        return "%s, vm:%s, suite:%s, args:'%s'" % (self.name, self.vm['name'], self.suite['name'], self.extra_args or '')
    
    def as_simple_string(self):
        if self.extra_args:
            return "%s (%s, %s, %s)"  % (self.name, self.vm['name'], self.suite['name'], self.extra_args)
        else:
            return "%s (%s, %s)"  % (self.name, self.vm['name'], self.suite['name'])
        
    def __eq__(self, other):
        """I am not exactly sure whether that will be right, or whether
           I actually need to take the whole suite and vm dictionaries
           into account"""
        if type(other) != type(self):
            return False
        
        return (    self.name           == other.name
                and self.extra_args     == other.extra_args
                and 0 == cmp(self.suite, other.suite)
                and 0 == cmp(self.vm,    other.vm))
                
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __hash__(self):
        return (hash(self.name) ^ 
                hash(self.extra_args) ^ 
                hash(self.suite['name']) ^
                hash(self.vm['name']))
    
    def as_tuple(self):
        return (self.name, self.vm['name'], self.suite['name'], self.extra_args)
    
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
