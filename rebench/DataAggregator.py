# Copyright (c) 2009-2011 Stefan Marr <http://www.stefan-marr.de/>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
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
import os
from datetime import datetime
from Executor import RunId
from copy import copy
import logging
import subprocess
import shutil
import time
from model.benchmark_config import BenchmarkConfig
from model.data_point       import DataPoint

class DataAggregator(object):

    def __init__(self, dataFileName, automaticallyPersistNewDataPoints = True):
        if not dataFileName:
            raise ValueError("DataAggregator expects a file name for dataFileName, but got: %s" % dataFileName)
        
        self._dataFileName   = dataFileName
        self._data = {}
        self._lastCriteria = None
        self._lastDataSet  = None
        self._automaticallyPersistNewDataPoints = automaticallyPersistNewDataPoints
        self._file    = None
        self._csvFile = None
    
    def discardOldData(self):
        self._truncateFile(self._dataFileName)
    
    def _truncateFile(self, fileName):
        with open(fileName, 'w'):
            pass
    
    def setCsvRawFile(self, csvRawFileName):
        """The CSV file is not the authoritative data source, lets reset it
           and recreate on the go."""
        self._truncateFile(csvRawFileName)
        self._csvFile = open(csvRawFileName, 'a+')
        
    def getData(self):
        return self._data
    
    def getDataWithUnfoldedConfig(self):
        """Unfold the config object to be able to query data better"""
        result = {}
        for cfg, items in self._data.iteritems():
            r = result
            cfgTuple = cfg.as_tuple()
            
            for i in cfgTuple[:-1]:
                r = r.setdefault(i, {})
            
            r[cfgTuple[-1]] = items
            
        return result
    
    def _flatten(self, data):
        result = {}
        self._flatten_((), data, result)
        return result
    
    def _flatten_(self, path, data, result):
        for key, val in data.iteritems():
            newPath = path + (key, )
            if type(val) is dict:
                self._flatten_(newPath, val, result)
            else:
                result[newPath] = val
    
    def getDataFlattend(self):
        """
        Returns a dictionary of all data with a tuple as the key.
        The key describes the used configuration.
        The data is the list of obtained values.
        """
        return self._flatten(self.getDataWithUnfoldedConfig())
    
    @classmethod
    def data_mapping(cls):
        """
        Returns a dictionary which describes the semantics of the indexes.
        Currently it is mostly used to look up the index of a certain
        property, thus, the dict contains 'parameter':index pairs.
        """
        standard_dimensions = {'cores' : 4, 'input_sizes' : 5, 'variable_values': 6}
        return dict(BenchmarkConfig.tuple_mapping(), **standard_dimensions) 
                                   
    
    def loadData(self):
        '''
        Loads the data from the configured data file
        '''
        errors = set()
        try:
            with open(self._dataFileName, 'r') as f:
                for line in f:
                    try:
                        # ignore shebang lines
                        if not line.startswith('#!'):
                            runId, value = self._deserializeDataPoint(line)
                            self.addDataPoints(runId, value, True)
                    except ValueError, e:
                        msg = str(e)
                        if msg not in errors:
                            # Configuration is not available, skip data point
                            logging.debug(msg)
                            errors.add(msg)
        except IOError:
            logging.info("No data loaded %s does not exist." % self._dataFileName)
                
    
    def includeShebangLine(self, argv):
        """
        Insert a shebang (#!/path/to/executable) into the data file, allows it to be executable
        """
        shebang_line = "#!%s\n" % (subprocess.list2cmdline(argv))
        
        try:
            if not os.path.exists(self._dataFileName):
                with open(self._dataFileName, 'w') as f:
                    f.write(shebang_line)
                    f.flush()
                    f.close()
                return
            
            renamed_file = "%s-%.0f.tmp" % (self._dataFileName, time.time()) 
            os.rename(self._dataFileName, renamed_file)
            with open(self._dataFileName, 'w') as f:
                f.write(shebang_line)
                f.flush()
                shutil.copyfileobj(open(renamed_file, 'r'), f)
            os.remove(renamed_file)
        except Exception as e:
            logging.error("An error occurred while trying to insert a shebang line: %s", e)
        
        
    def getDataSet(self, runId, createDataStructures = True):
        """
        Returns the data set identified by ``runId``
        If ``createDataStructures`` == True, missing levels in
        the data structures will be created.
        
        We also added a simple caching, to avoid to much traversal.
        I know, premature optimization...
        """
        
        criteria = (runId.cfg, ) + runId.variables
        
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
                
                for point in value:
                    if self._automaticallyPersistNewDataPoints and not deserializing:
                        self._persistDataPoint(tmpRunId, point)
                    self._persistDataPointAsCSV(tmpRunId, point)

#                assert len(value) == 1
#                if self._automaticallyPersistNewDataPoints and not deserializing:
#                    self._persistDataPoint(tmpRunId, value[0])
#                self._persistDataPointAsCSV(tmpRunId, value[0])
    
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
    
    def _persistDataPointAsCSV(self, runId, dataPoint):
        if self._csvFile:
            self._csvFile.writelines(self._serializeDataPointAsCSV(runId, dataPoint))
            self._csvFile.flush()
        
    def _serializeDataPoint(self, runId, dataPoint):
        result = []
        result.append("[%s]" % datetime.now())
        
        criteria = (runId.cfg, ) + runId.variables + (runId.criterion, )
        
        for criterion in criteria:
            result.append("\t%s" % criterion)
            
        result.append(" = %f\n" % dataPoint)
        
        return result
    
    def _serializeDataPointAsCSV(self, runId, dataPoint):
        result = []
        runCfg = runId.cfg.as_tuple()
        # the extra args are often more complex, lets protect them with ""
        
        
        criteria = runCfg[:-1] + ("\"%s\""%runCfg[-1],) + runId.variables + (runId.criterion, )
        #tuple(["\"%s\""%x for x in runId.variables])
        result.append("%f" % dataPoint)
        
        for criterion in criteria:
            result.append("\t%s" % criterion)
        
        result.append("\n")
        
        return result
    
    _parseRegex = re.compile(r"\[.*?\]" "\t" r"(.*?), vm:(.*?), suite:(.*?), args:'(.*?)'((?:" "\t"  r"(?:.*?))+) = (.*)")
    
    def _deserializeDataPoint(self, line):
        m = self._parseRegex.match(line)
        benchName = m.group(1)
        vmName = m.group(2)
        suiteName = m.group(3)
        args = m.group(4) if m.group(4) else None
        restRunId = m.group(5).strip().split("\t")
        
        cfg = BenchmarkConfig.get_config(benchName, suiteName, vmName, args)
        
        criterion = restRunId[-1]
        restRunId = restRunId[:-1]
        dataPoint = DataPoint(float(m.group(6)), None, criterion)
        
        return RunId(cfg, restRunId, criterion), dataPoint
