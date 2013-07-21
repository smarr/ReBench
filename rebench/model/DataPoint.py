class DataPoint:
    def __init__(self, time, benchName = None, criterion = 'total'):
        self._benchName = benchName
        self._criterion = criterion
        self._time = time
        
    def is_total(self):
        return self._criterion == 'total'
    
    @property
    def benchName(self):
        return self._benchName
    
    @property
    def criterion(self):
        return self._criterion
    
    @property
    def time(self):
        return self._time
