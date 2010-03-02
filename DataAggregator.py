'''
Created on Feb 28, 2010

The data aggregator supports the following data dimensions:

  - VM
  - input size
  - number of cores
  - benchmark
  - an additional free variable
  
  These are the dimensions over which the benchmark runs vary.
  
  Furthermore, a single benchmark run can produce multiple results,
  which are combined to a data point.
  
  For example the NPB Integer Sort benchmark generates
  results for the different phases:
     keyInit, phase1, phase2, verifyComplete, total
  Thus, a data point is either a ``float`` value, or a dict containing
  different criteria.
  
  These results still constitute one datapoint.
  Points are generated as long as the desired statistic properties are not
  satisfied and eventually constitute a single 'run'.
  
  'runs' are varied over the above mentioned variables.
  All variations constitute over the runs constitute a suite.
  
  This leads to: point < run < suite 


  @author: smarr
'''

class DataAggregator(object):
    '''
    classdocs
    '''


    def __init__(self, dataFileName, automaticallyPersistNewDataPoints = True):
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
    
    def addDataPoint(self, runId, dataPoint):
        """
        Add the data point to the run which is indicated by the given
        ``runId``
        """
        dataSet = self.getDataSet(runId)
        dataSet.append(dataPoint)
        
        if self.automaticallyPersistNewDataPoints:
            self._persistDataPoint(runId, dataPoint)
    
    def saveData(self):
        # we need that only if it is not done automatically
        if not self.automaticallyPersistNewDataPoints:
            self._persistData()

    def _persistDataPoint(self, runId, dataPoint):
        pass
