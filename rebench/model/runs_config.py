class RunsConfig(object):
    """ General configuration parameters for runs """
    def __init__(self,
                 number_of_data_points = None,
                 min_runtime           = None):
        self._number_of_data_points = number_of_data_points
        self._min_runtime           = min_runtime
    
    @property
    def number_of_data_points(self):
        return self._number_of_data_points
        
    @property
    def min_runtime(self):
        return self._min_runtime
    
    @property
    def is_quick(self):
        return False
    
    def combined(self, runDef):
        config = RunsConfig(self._number_of_data_points, self._min_runtime)
        val = runDef.get('number_of_data_points', None)
        if val:
            config._number_of_data_points = val
        val = runDef.get('min_runtime', None)
        if val:
            config._min_runtime = val
        return config
    
    def log(self, logging):
        msg = "Run Config: number of data points: %d" % (self._number_of_data_points)
        if self._min_runtime:
            msg += ", min_runtime: %dms" % (self._min_runtime)
        logging.debug(msg)

class QuickRunsConfig(RunsConfig):
    
    def __init__(self, number_of_data_points = None,
                       min_runtime           = None,
                       max_time              = None):
        super(QuickRunsConfig, self).__init__(number_of_data_points,
                                              min_runtime)
        self._max_time = max_time
    
    @property
    def is_quick(self):
        return True
    
    @property
    def max_time(self):
        return self._max_time
