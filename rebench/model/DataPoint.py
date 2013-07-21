class DataPoint:
    def __init__(self, time, benchName = None, criterion = 'total'):
        self.benchName = benchName
        self.criterion = criterion
        self.time = time
        
    def is_total(self):
        return self.criterion == 'total'
