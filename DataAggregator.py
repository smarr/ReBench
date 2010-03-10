'''
Created on Feb 28, 2010

The data aggregator supports the following data dimensions:

  - VM
  - input size
  - number of cores
  - benchmark
  - an additional free variable
  
  These are the dimensions over which the benchmark suite varies its
  configurations.
  
  Furthermore, a single benchmark configuration can produce multiple results,
  which are combined to a data point.
  
  For example the NPB Integer Sort benchmark generates
  results for the different phases:
     keyInit, phase1, phase2, verifyComplete, total
  Thus, a data point is either a ``float`` value, or a dict containing
  different criteria.
  
  These results still constitutes one datapoint.
  Points are generated as long as the desired statistic properties are not
  satisfied and eventually constitute a single 'run'.
  
  'runs' are varied over the above mentioned variables.
  All variations constitute over the runs constitute a suite.
  
  This leads to: point < configuration < suite < runs 


  @author: smarr
'''

class DataAggregator(object):
    '''
    classdocs
    '''


    def __init__(self, dataFileName, discardOldData, automaticallyPersistNewDataPoints = True):
        '''
        Constructor
        '''
        self._dataFileName = dataFileName
        self._data = {}
        self._lastRunId = None
        self._lastDataSet = None
        self._automaticallyPersistNewDataPoints = automaticallyPersistNewDataPoints
    
    def loadData(self):
        '''
        Loads the data from the configured data file
        '''
        pass
    
    def getDataSet(self, runId, createDataStructures = True):
        """
        Returns the data set identified by ``runId``
        If ``createDataStructures`` == True, missing levels in
        the data structures will be created.
        
        We also added a simple caching, to avoid to much traversal.
        I know, premature optimization...
        """
        
        if runId == self._lastRunId:
            return self._lastDataSet
        
        previous = None
        dataSet = self._data
        
        for criteria in runId:
            assert type(dataSet) is dict
            
            if dataSet.has_key(criteria):
                pass  # nothing to do here, but ``if`` looks readable
            elif createDataStructures:
                dataSet[criteria] = {}
            else:
                return None
            
            previous = dataSet
            dataSet = dataSet[criteria]
        
        if type(previous[runId[-1]]) is dict:
            previous[runId[-1]] = []  ## should be a list of datapoints instead
            dataSet = previous[runId[-1]]
            
        assert type(dataSet) is list
        
        self._lastDataSet = dataSet
        self._lastRunId   = runId
        
        return dataSet
    
    def getNumberOfDataPoints(self, runId):
        return len(self.getDataSet(runId))
    
    def getDataSample(self, runId, criterion = "total"):
        """
        Returns the plain data for a run and a chosen criterion.
        This is necessary for the statistical computations.
        
        Plain data is returned as a list of values.
        """
        dataSet = self.getDataSet(runId)
        if type(dataSet[0]) is dict:
            return list(val[criterion] for val in dataSet)
        else:
            return dataSet
    
    def _flattenData(self, dataPoints):
        benchmarks = {}
        
        for point in dataPoints:
            benchmarks.setdefault(point.benchName, {}).setdefault(point.criterion, []).append(point.time)
            
        return benchmarks
    
    def addDataPoints(self, runId, dataPoints):
        """
        Add the data point to the run which is indicated by the given
        ``runId``.
        Data points itself can be from different benchmarks of the same run
        or contain different criteria, so we are going to sort that out first.
        """
        origRunId = runId
        flatData = self._flattenData(dataPoints)
        
        if None in flatData:
            assert len(flatData) == 1
        
        for bench, criteria in flatData.iteritems():
            for criterion, value in criteria.iteritems():
                assert type(value[0]) is float
                
                runId = origRunId
                if bench is not None:
                    runId = runId + (bench,)
                if criterion is not None:
                    runId = runId + (criterion,)
                
                dataSet = self.getDataSet(runId)
                dataSet += value
        
                if self._automaticallyPersistNewDataPoints:
                    self._persistDataPoint(runId, value)
    
    def saveData(self):
        # we need that only if it is not done automatically
        if not self.automaticallyPersistNewDataPoints:
            self._persistData()

    def _persistDataPoint(self, runId, dataPoint):
        pass

class DataPoint:
    def __init__(self, time, benchName = None, criterion = 'total'):
        self.benchName = benchName
        self.criterion = criterion
        self.time = time
        
    def isTotal(self):
        return self.criterion == 'total'