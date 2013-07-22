class Statistics(object):
    def __init__(self,
                 max_runs = None,
                 min_runs = None,
                 error_margin     = None,
                 confidence_level = None,
                 min_runtime      = None):
        self._max_runs         = max_runs
        self._min_runs         = min_runs
        self._error_margin     = error_margin
        self._confidence_level = confidence_level
        self._min_runtime      = min_runtime
    
    @property
    def max_runs(self):
        return self._max_runs
    
    @property
    def min_runs(self):
        return self._min_runs
    
    @property
    def error_margin(self):
        return self._error_margin
    
    @property
    def confidence_level(self):
        return self._confidence_level
    
    @property
    def min_runtime(self):
        return self._min_runtime
    
    def combine(self, values):
        stats = Statistics(**values)
        stats.__dict__.update(self.__dict__)
        return stats
    
