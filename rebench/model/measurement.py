class Measurement:
    def __init__(self, value, bench_name = None, criterion = 'total', unit = None):
        self._bench_name = bench_name
        self._criterion  = criterion
        self._value      = value
        
    def is_total(self):
        return self._criterion == 'total'
    
    @property
    def bench_name(self):
        return self._bench_name
    
    @property
    def criterion(self):
        return self._criterion
    
    @property
    def value(self):
        return self._value
    
    @property
    def unit(self):
        return self._unit
