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

import re
from datetime import datetime
from Configurator import BenchmarkConfig
from Executor import RunId
from copy import copy
import logging

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
        self._lastCriteria = None
        self._lastDataSet = None
        self._automaticallyPersistNewDataPoints = automaticallyPersistNewDataPoints
        self._file = None
        
        if discardOldData:
            with open(self._dataFileName, 'w'):
                pass
        
        self.loadData()
        
    def getData(self):
        return self._data
    
    def loadData(self):
        '''
        Loads the data from the configured data file
        '''
        try:
            with open(self._dataFileName, 'r') as f:
                for line in f:
                    runId, value = self._deserializeDataPoint(line)
                    self.addDataPoints(runId, value, True)
        except IOError:
            logging.info("No data loaded %s does not exist." % self._dataFileName)
                
    
    def getDataSet(self, runId, createDataStructures = True):
        """
        Returns the data set identified by ``runId``
        If ``createDataStructures`` == True, missing levels in
        the data structures will be created.
        
        We also added a simple caching, to avoid to much traversal.
        I know, premature optimization...
        """
        
        criteria = (runId.cfg, ) + runId.variables + (runId.criterion, )
        
        if criteria == self._lastCriteria:
            return self._lastDataSet
        
        previous = None
        dataSet = self._data
        
        for criterion in criteria:
            if type(dataSet) is not dict:
                pass
            assert type(dataSet) is dict, "last dataSet is of type %s instead of being a dict (criteria: %s, runId: %s)" % (type(dataSet), criterion, runId)
            
            if criterion in dataSet:
                pass  # nothing to do here, but ``if`` looks readable
            elif createDataStructures:
                dataSet[criterion] = {}
            else:
                return None
            
            previous = dataSet
            dataSet = dataSet[criterion]
        
        if type(dataSet) is dict:       #equals type(previous[runId[-1]]) is dict
            if len(dataSet) == 0: 
                previous[criteria[-1]] = []  ## should be a list of datapoints instead
                dataSet = previous[criteria[-1]]
            
        assert type(dataSet) is list
        
        self._lastDataSet = dataSet
        self._lastCriteria= criteria
        
        return dataSet
    
    def getNumberOfDataPoints(self, runId):
        return len(self.getDataSet(runId))
    
    def getDataSample(self, runId):
        """
        Returns the plain data for a run and a chosen criterion.
        This is necessary for the statistical computations.
        
        Plain data is returned as a list of values.
        """
        return self.getDataSet(runId)
        #REMOVE: TODO:
        #if type(dataSet[0]) is dict:
        #    return list(val[criterion] for val in dataSet)
        #else:
        #    return dataSet
    
    def _flattenData(self, dataPoints):
        benchmarks = {}
        
        if type(dataPoints) is list:
            for point in dataPoints:
                benchmarks.setdefault(point.benchName, {}).setdefault(point.criterion, []).append(point.time)
        else:
            benchmarks.setdefault(dataPoints.benchName, {}).setdefault(dataPoints.criterion, []).append(dataPoints.time)
        
        return benchmarks
    
    def addDataPoints(self, runId, dataPoints, deserializing = False):
        """
        Add the data point to the run which is indicated by the given
        ``runId``.
        Data points itself can be from different benchmarks of the same run
        or contain different criteria, so we are going to sort that out first.
        """
        flatData = self._flattenData(dataPoints)
        
        if None in flatData:
            assert len(flatData) == 1
        
        for bench, criteria in flatData.iteritems():
            for criterion, value in criteria.iteritems():
                assert type(value[0]) is float
                
                tmpRunId = copy(runId)
                
                if bench is not None and bench != 'total':
                    tmpRunId.variables += (bench,)
                
                if criterion is not None:
                    # here we encode, that there might be a benchmark name total
                    # which generates data for the criterion total, 
                    # but for nothing else
                    if criterion == 'total' and bench == 'total':
                        assert len(criteria) == 1
                    
                    tmpRunId.criterion = criterion
                
                dataSet = self.getDataSet(tmpRunId)
                dataSet += value
        
                assert len(value) == 1
                if self._automaticallyPersistNewDataPoints and not deserializing:
                    self._persistDataPoint(tmpRunId, value[0])
    
    def saveData(self):
        # we need that only if it is not done automatically
        if not self.automaticallyPersistNewDataPoints:
            self._persistData()

    def _openFileToAddNewData(self):
        if not self._file:
            self._file = open(self._dataFileName, 'a+')

    def _persistDataPoint(self, runId, dataPoint):
        self._openFileToAddNewData()
        
        self._file.writelines(self._serializeDataPoint(runId, dataPoint))
        self._file.flush()
        
    def _serializeDataPoint(self, runId, dataPoint):
        result = []
        result.append("[%s]" % datetime.now())
        
        criteria = (runId.cfg, ) + runId.variables + (runId.criterion, )
        
        for criterion in criteria:
            result.append("\t%s" % criterion)
            
        result.append(" = %f\n" % dataPoint)
        
        return result
    
    _parseRegex = re.compile(r"\[.*?\]" "\t" r"(.*?), vm:(.*?), suite:(.*?), args:'(.*?)'((?:" "\t"  r"(?:.*?))+) = (.*)")
    
    def _deserializeDataPoint(self, line):
        m = DataAggregator._parseRegex.match(line)
        benchName = m.group(1)
        vmName = m.group(2)
        suiteName = m.group(3)
        args = m.group(4) if m.group(4) else None
        restRunId = m.group(5).strip().split("\t")
        
        cfg = BenchmarkConfig.getConfig(benchName, suiteName, vmName, args)
        
        criterion = restRunId[-1]
        restRunId = restRunId[:-1]
        dataPoint = DataPoint(float(m.group(6)), None, criterion)
        
        return RunId(cfg, restRunId, criterion), dataPoint

class DataPoint:
    def __init__(self, time, benchName = None, criterion = 'total'):
        self.benchName = benchName
        self.criterion = criterion
        self.time = time
        
    def isTotal(self):
        return self.criterion == 'total'
