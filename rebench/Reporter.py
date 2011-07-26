# Copyright (c) 2009 Stefan Marr
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from __future__ import with_statement
from datetime import datetime
import logging
from copy import copy
from Statistics import StatisticProperties
from contextpy import layer, after, globalActivateLayer
from DataAggregator import DataAggregator
import json
import urllib2
import urllib
import re
import locale
# proceed, activelayer, activelayers, around, before, base,

try:
    import matplotlib
    #check http://matplotlib.sourceforge.net/faq/installing_faq.html#what-is-a-backend for backends
    matplotlib.use('AGG') #PDF crashes with test.conf :(

    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon
except ImportError:
    logging.info("matplotlib was not found, import failed: " + str(ImportError))

benchmark = layer("benchmark")
profile = layer("profile")
log_to_file = layer("log_to_file")

class Reporter:

    # only domain specific stuff here..., we are not interested in the details
    # and general logging here
    #def info(self, msg, level = None):
    #    pass
    #
    #def warning(self, msg, level = None):
    #    pass
    #
    #def failure(self, msg, level = None):
    #    pass
    #
    #def beginSeparatLog(self, task, level = None):
    #    pass
    #
    #def endSeparatLog(self, task, level = None):
    #    pass
    
    def runFailed(self, runId):
        raise NotImplementedError('Subclass responsibility')
    
    def configurationCompleted(self, runId, statistics):
        raise NotImplementedError('Subclass responsibility')
    
    def jobCompleted(self, configurations, dataAggregator):
        raise NotImplementedError('Subclass responsibility')

class Reporters(Reporter):
    """Distributes the information to all registered reporters."""
    
    def __init__(self, reporters):
        if type(reporters) is list:
            self._reporters = reporters
        else:
            self._reporters = [reporters]

    def runFailed(self, runId):
        for reporter in self._reporters:
            reporter.runFailed(runId)
            
    def configurationCompleted(self, runId, statistics):
        for reporter in self._reporters:
            reporter.configurationCompleted(runId, statistics)
    
    def jobCompleted(self, configurations, dataAggregator):
        for reporter in self._reporters:
            reporter.jobCompleted(configurations, dataAggregator)

class TextReporter(Reporter):
    
    def __init__(self, configurator):
        self._configurator = configurator
    
    def _configuration_details(self, runId, statistics = None):
        result = []
        
        criteria = (runId.cfg, ) + runId.variables + (runId.criterion, )
        
        for criterion in criteria:
            result.append(" %s" % criterion)
            
        result.append(" = ")
        
        self._output_stats(result, statistics)
            
        return result
    
    def _output_stats(self, outputList, statistics):
        if not statistics:
            return
        
        for field, value in statistics.__dict__.iteritems():
            if not field.startswith('_'):
                outputList.append("%s: %s " % (field, value))
    
    def _generate_all_output(self, data, path):
        assert type(data) is dict or type(data) is list
        
        if type(data) is dict:
            for key, val in data.iteritems():
                for result in self._generate_all_output(val, path + (key,)):
                    yield result
        else:
            stats = StatisticProperties(data, 
                                        self._configurator.statistics['confidence_level'])
            
            out = []
            for item in path:
                out.append(str(item))
                
            out = [ " ".join(out) + " " ]
            
            self._output_stats(out, stats)
            
            result = "".join(out)
            yield result

class CliReporter(TextReporter):
    """ Reports to standard out using the logging framework """
    
    def __init__(self, configurator):
        TextReporter.__init__(self, configurator)

    def runFailed(self, runId):
        result = []
        result.append("[%s] Run failed: " % datetime.now())

        result += self._configuration_details(runId) 

        result.append("\n")

        result = "".join(result)

        logging.debug(result)    

    def configurationCompleted(self, runId, statistics):
        result = []
        result.append("[%s] Configuration completed: " % datetime.now())
        
        result += self._configuration_details(runId, statistics) 
            
        result.append("\n")
        
        result = "".join(result)
        
        logging.debug(result)

    def jobCompleted(self, configurations, dataAggregator):
        logging.info("[%s] Job completed" % datetime.now())
        for line in self._generate_all_output(dataAggregator.getData(), ()):
            logging.info(line)
    
    

class FileReporter(TextReporter):
    """ should be mainly a log file
        data is the responsibility of the DataAggregator
    """
    
    def __init__(self, fileName, configurator):
        TextReporter.__init__(self, configurator)
        self._file = open(fileName, 'a+')

    def runFailed(self, runId):
        result = []
        result.append("[%s] Run failed: " % datetime.now())

        result += self._configuration_details(runId) 

        result.append("\n")

        self._file.writelines(result)
        
    def configurationCompleted(self, runId, statistics):
        result = []
        result.append("[%s] Configuration completed: " % datetime.now())
        
        result += self._configuration_details(runId, statistics) 
            
        result.append("\n")
        
        self._file.writelines(result)
    
    def jobCompleted(self, configurations, dataAggregator):
        self._file.write("[%s] Job completed\n" % datetime.now())
        for line in self._generate_all_output(dataAggregator.getData(), ()):
            self._file.write(line + "\n")
            
        self._file.close()
            
class CSVFileReporter(Reporter):
    """ Will generate a CSV file for processing in another program as for instance Excel or Numbers """
    
    def __init__(self, configurator):
        self._file = open(configurator.reporting['csv_file'], 'a+')
        self._configurator = configurator
    
    def runFailed(self, runId):
        pass
    
    def configurationCompleted(self, runId, statistics):
        pass
    
    def _prepareHeaderRow(self, data, dataAggregator, parameterMappings):
        # since the data might be irregular find the item with the most parameters first
        longestTuple = max(data.keys(), key=lambda tpl: len(tpl))
        # and determine table width
        table_width = len(longestTuple)
        
        # now generate the header
        
        # get sorted parameter mapping first
        mapping = sorted(parameterMappings.items(), key=lambda entry:  entry[1])
        
        header_row = []
        for (title, _index) in mapping:
            header_row.append(title)
        
        # add empty columns to keep table aligned    
        while len(header_row) < table_width:
            header_row.append('')
        
        # now the statistic rows
        for title in StatisticProperties.tuple_mapping():
            header_row.append(title)
        
        return header_row, table_width
    
    def jobCompleted(self, configurations, dataAggregator):
        old_locale = locale.getlocale(locale.LC_ALL)
        if 'csv_locale' in self._configurator.reporting:
            locale.setlocale(locale.LC_ALL, self._configurator.reporting['csv_locale'])
        
        
        # get the data to be processed
        data = dataAggregator.getDataFlattend()
        parameterMappings = dataAggregator.data_mapping()
        num_common_parameters = len(parameterMappings)
        
        header_row, max_num_parameters = self._prepareHeaderRow(data, dataAggregator, parameterMappings)
        
        table = []
        
        # add the header row
        table.append(header_row)
        
        # add the actual results to the table
        for run, measures in data.iteritems():
            row = []
            row += run[0 : num_common_parameters]                 # add the common ones
            row += [''] * (max_num_parameters - len(run))         # add fill for unused parameters
            row += run[num_common_parameters : ]                  # add all remaining
            row += list(StatisticProperties(measures, 
                            self._configurator.statistics['confidence_level']).as_tuple()) # now add the actual result data
            table.append(row)
        
        for row in table:
            self._file.write(";".join([i if type(i) == str else locale.format("%f", i or 0.0) for i in row]) + "\n")
            
        self._file.close()
        locale.setlocale(locale.LC_ALL, old_locale)
        

class CodespeedReporter(Reporter):
    """
    This report will report the recorded data on the completion of the job
    to the configured Codespeed instance.
    """
    
    def __init__(self, configurator):
        self._configurator = configurator
        self._incremental_report = self._configurator.options.report_incrementally
        
        # ensure that all necessary configurations have been set
        if self._configurator.options.commit_id is None:
            raise ValueError("--commit-id has to be set on the command line for codespeed reporting.")
        if self._configurator.options.environment is None:
            raise ValueError("--environment has to be set on the command line for codespeed reporting.")
        self._codespeed_cfg = self._configurator.reporting['codespeed']
        
        if "project" not in self._codespeed_cfg:
            raise ValueError("The config file needs to configure a 'project' in the reporting.codespeed section")
        if "url" not in self._codespeed_cfg:
            raise ValueError("The config file needs to configure a URL to codespeed in the reporting.codespeed section")

        
        # contains the indexes into the data tuples for
        # the parameters
        self._indexMap = DataAggregator.data_mapping()
        
    def runFailed(self, runId):
        pass


    def configurationCompleted(self, runId, statistics):
        if not self._incremental_report:
            return
        
        # if self._incremental_report is true we are going to talk to codespeed immediately
        results = [self._formatForCodespeed(runId.as_tuple(), statistics)]
        
        # now, send them of to codespeed
        self._sendToCodespeed(results)
    
    def _result_data_template(self):
        # all None values have to be filled in
        return {
            'commitid':     self._configurator.options.commit_id,
            'project':      self._codespeed_cfg['project'],
            #'revision_date': '', # Optional. Default is taken
                                  # either from VCS integration or from current date
            'executable':   None,
            'benchmark':    None,
            'environment':  self._configurator.options.environment,
            'branch':       self._configurator.options.branch,
            'result_value': None,
            # 'result_date': datetime.today(), # Optional
            'std_dev':      None,
            'max':          None,
            'min':          None }

    def _beautifyBenchmarkName(self, name):
        """
        Currently just remove all bench, or benchmark strings.
        """
        replace = re.compile('bench(mark)?', re.IGNORECASE)
        return replace.sub('', name)

    def _formatForCodespeed(self, run, stats = None):
        result = self._result_data_template()
        
        if stats and not stats.failedRun:
            result['min']          = stats.min
            result['max']          = stats.max
            result['std_dev']      = stats.stdDev
            result['result_value'] = stats.mean
        else:
            result['result_value'] = -1
        
        if self._configurator.options.executable is None:
            result['executable']   = run[self._indexMap['vm']]
        else:
            result['executable']   = self._configurator.options.executable

        
        # TODO: make that configurable and find a way
        #       that the place holder expansion is done in a sane and consistent way
        name = self._beautifyBenchmarkName(run[self._indexMap['bench']])
        name = "%s (%s cores, %s %s)" % (name, run[self._indexMap['cores']] or "",
                                               run[self._indexMap['input_sizes']] or "",
                                               run[self._indexMap['extra_args']] or "")
        name = name % {'cores' : run[self._indexMap['cores']] }
        result['benchmark'] = name
        
        return result

    def _prepareResult(self, run, measures):
        if measures:
            # get the statistics
            stats = StatisticProperties(measures, self._configurator.statistics['confidence_level'])
        else:
            stats = None
            
        return self._formatForCodespeed(run, stats)
    
    def _sendToCodespeed(self, results):
        payload = urllib.urlencode({'json' : json.dumps(results) })
        
        try:
            fh = urllib2.urlopen(self._codespeed_cfg['url'], payload)
            response = fh.read()
            fh.close()
            logging.info("Results were sent to codespeed, response was: " + response)
        except urllib2.HTTPError as error:
            logging.error(str(error) + " This is most likely caused by either " +
                   "a wrong URL in the config file, or an environment not " +
                   "configured in codespeed. URL: " +
                   self._codespeed_cfg['url'])
        

    def jobCompleted(self, configurations, dataAggregator):
        if self._incremental_report:
            # in this case all duties are already completed
            return
        
        # get the data to be processed
        data = dataAggregator.getDataFlattend()
        
        # create a list of results to be submitted
        results = []
        for run, measures in data.iteritems():
            results.append(self._prepareResult(run, measures))
        
        # now, send them of to codespeed
        self._sendToCodespeed(results)


class DiagramResultReporter(Reporter):
    
    def __init__(self, configurator):
        self._configurator = configurator
        self._separateByMapping = DataAggregator.data_mapping()
        self._separateByIndexes = None

    def runFailed(self, runId):
        pass

    
    def configurationCompleted(self, runId, statistics):
        pass
    
    def jobCompleted(self, configurations, dataAggregator):
        
        data = dataAggregator.getDataWithUnfoldedConfig()
        data = self._filter_by_criterion(data)
        data = self._separate(data)
        data = self._group(data)
        data = self._sort(data)
        
        for characteristics, groups in data.iteritems():
            self._createDiagram(characteristics, groups)
        
    
    def _createDiagram(self, character, groups):
        assert type(character) is tuple, "character was expected to be a tuple but is " + str(type(character)) + ":" + str(character)
        assert type(groups) is dict
        
        try:
            fileName = self._configurator.visualization.get('fileName', "%s-%s.pdf") % character
        except TypeError:
            raise ValueError("fileName template given in configuration does not match the given arguments. Tpl: " + self._configurator.visualization.get('fileName', "%s-%s.pdf") + " args: " + character.__str__())
        
        fig, ax1 = self._createFigure()
        data, titles = self._prepareData(groups)
        
        self._estimanteInterval(data)
        
        bp = self._plotBoxes(data)
        self._brushUpBoxes(bp, data, ax1)
        
        self._addDataLabels(ax1, titles, len(data))
        self._addAdditionalXAxisValueLabels(len(bp['boxes']), ax1)
        self._addLegend()
        
        plt.savefig(fileName)
        
    def _estimanteInterval(self, data):
        result = []
        for list in data:
            result += list
            
        self._top = max(result)    if result else 0
        self._bottom = min(result) if result else 0
        
    def _addLegend(self):
        # Finally, add a basic legend
        return
    
        plt.figtext(0.80, 0.08,  '500 Random Numbers' ,
                   backgroundcolor=self._boxColors[0], color='black', weight='roman',
                   size='x-small')
        plt.figtext(0.80, 0.045, 'IID Bootstrap Resample',
        backgroundcolor=self._boxColors[1],
                   color='white', weight='roman', size='x-small')
        plt.figtext(0.80, 0.015, '*', color='white', backgroundcolor='silver',
                   weight='roman', size='medium')
        plt.figtext(0.815, 0.013, ' Average Value', color='black', weight='roman',
                   size='x-small')

        
    def _addAdditionalXAxisValueLabels(self, numBoxes, ax1):
        # Due to the Y-axis scale being different across samples, it can be
        # hard to compare differences in medians across the samples. Add upper
        # X-axis tick labels with the sample medians to aid in comparison
        # (just use two decimal places of precision)
        pos = np.arange(numBoxes)+1
        upperLabels = [str(np.round(s, 2)) for s in self._medians]
        weights = ['bold', 'semibold']
        for tick,label in zip(range(numBoxes),ax1.get_xticklabels()):
            k = tick % 2
            ax1.text(pos[tick], self._top-(self._top*0.05), upperLabels[tick],
                     horizontalalignment='center', size='x-small', weight=weights[k],
                     color=self._boxColors[k])
    
    def _addDataLabels(self, ax1, titles, numBoxes):
        # Set the axes ranges and axes labels
        ax1.set_xlim(0.5, numBoxes+0.5)
        ax1.set_ylim(self._bottom, self._top)
        xtickNames = plt.setp(ax1, xticklabels=titles)
        plt.setp(xtickNames, rotation=90, fontsize=8)
    
    def _createFigure(self):
        title = self._configurator.visualization.get('title', '')
        fig = plt.figure(figsize=(10,6))
        #fig.canvas.set_window_title(title)
        ax1 = fig.add_subplot(111)
        plt.subplots_adjust(left=0.075, right=0.95, top=0.9, bottom=0.25)

        # Add a horizontal grid to the plot, but make it very light in color
        # so we can use it for reading data values but not be distracting
        ax1.yaxis.grid(True, linestyle='-', which='major', color='lightgrey',
              alpha=0.5)
        
        # Hide these grid behind plot objects
        ax1.set_axisbelow(True)
        ax1.set_title(title)
        ax1.set_xlabel(self._configurator.visualization.get('labelXAxis', ''))
        ax1.set_ylabel(self._configurator.visualization.get('labelYAxis', ''))
        
        return fig, ax1
    
    def _plotBoxes(self, data):
        bp = plt.boxplot(data, notch=0, sym='+', vert=1, whis=1.5)
        plt.setp(bp['boxes'], color='black')
        plt.setp(bp['whiskers'], color='black')
        plt.setp(bp['fliers'], color='red', marker='+')
        
        return bp
    
    def _brushUpBoxes(self, bp, data, ax1):
        # Now fill the boxes with desired colors
        self._boxColors = ['darkkhaki','royalblue']
        numBoxes = len(bp['boxes']) #len(data)
        
        if numBoxes != len(bp['boxes']):
            foo
        
        assert numBoxes == len(bp['boxes'])
        
        self._medians = range(numBoxes)
        for i in range(numBoxes):
            box = bp['boxes'][i]
            boxX = []
            boxY = []
            for j in range(5):
                boxX.append(box.get_xdata()[j])
                boxY.append(box.get_ydata()[j])
            boxCoords = zip(boxX,boxY)
            # Alternate between Dark Khaki and Royal Blue
            k = i % 2
            boxPolygon = Polygon(boxCoords, facecolor=self._boxColors[k])
            ax1.add_patch(boxPolygon)
            # Now draw the median lines back over what we just filled in
            med = bp['medians'][i]
            medianX = []
            medianY = []
            for j in range(2):
                medianX.append(med.get_xdata()[j])
                medianY.append(med.get_ydata()[j])
                plt.plot(medianX, medianY, 'k')
                self._medians[i] = medianY[0]
            # Finally, overplot the sample averages, with horixzontal alignment
            # in the center of each box
            plt.plot([np.average(med.get_xdata())], [np.average(data[i])],
                   color='w', marker='*', markeredgecolor='k')
    
    def _prepareData(self, groups):
        if 'columnName' in self._configurator.visualization:
            columnName = self._configurator.visualization['columnName']
        else:
            columnName = None
        
        #hm, ignore grouping for now, we will incooperate that later if necessary
        data = []
        titles = []
        for group, values in groups.iteritems():
            tmpTitles, tmpVals = zip(*values)
            
            def name(tuple):
                if columnName:
                    return columnName.format(*tuple)
                else:
                    return str(tuple)
            
            data += tmpVals
            
            for title in tmpTitles:
                if type(group) is str:
                    titles.append(name((group,) + title))
                else:
                    titles.append(name(group + title))
        
        return data, titles
        
    
    def _filter_by_criterion(self, data):
        if 'criterion' in self._configurator.visualization:
            return self._filter_by_criterion_(data, self._configurator.visualization['criterion'])
        else:
            return data
        
    def _filter_by_criterion_(self, data, criterion):
        assert type(data) is dict
        
        result = {}
        
        for key, val in data.iteritems():
            if type(val) is dict:
                result[key] = self._filter_by_criterion_(val, criterion)
            else:
                assert type(val) is list
                # rem: that is not correct, from a strict point of view, we are not ensuring,
                #      that all values in the dict are lists...
                if key == criterion:
                    return val
        
        return result
    
    def _separate(self, data):
        if 'separateBy' in self._configurator.visualization:
            separateBy =  self._configurator.visualization['separateBy']
            if type(separateBy) is not list:
                separateBy = [separateBy]
                
            return self._separate_(data, separateBy)
        else:
            return data
        
    def _separate_(self, data, separateBy):
        separateByIndexes = []
        for dimName in separateBy:
            assert dimName in self._separateByMapping, "The separateBy criterion '%s' you used is not known, has to be specified in DiagramResultReporter()._separateByMapping" % dimName
            dim = self._separateByMapping[dimName]
            separateByIndexes.append(dim)
        
        self._separateByIndexes = separateByIndexes
        
        result = {}
        self._separate__(data, (), result, (), separateByIndexes)
        
        return result
        
    def _separate__(self, data, path, result, separateBy, separateByIndexes):
        if type(data) is dict:
            for key, val in data.iteritems():
                newPath = path
                newSeparateBy = separateBy
                if (len(path) + len(separateBy)) in separateByIndexes:
                    newSeparateBy += (key,)
                else:
                    newPath += (key,)
                
                self._separate__(val, newPath, result, newSeparateBy, separateByIndexes)
        else:
            assert type(data) is list
            
            result = result.setdefault(separateBy, {})
            
            for item in path[:-1]:
                result = result.setdefault(item, {})
            
            result[path[-1]] = data

    def _group(self, data):
        if 'groupBy' in self._configurator.visualization:
            groupBy =  self._configurator.visualization['groupBy']
            if type(groupBy) is not list:
                groupBy = [groupBy]
                
            return self._group_(data, groupBy)
        else:
            return data
        
    def _group_(self, data, groupBy):
        indexes = []
        for dimName in groupBy:
            assert dimName in self._separateByMapping, "The separateBy criterion '%s' you used is not known, has to be specified in DiagramResultReporter()._separateByMapping" % dimName
            dim = self._separateByMapping[dimName]
            origDim = dim
            # we need to adjust them since we might have separated out data already
            for sepI in self._separateByIndexes:
                assert sepI != origDim, "You can not groupBy '%s' since it was already separated out" % dimName
                if sepI < origDim:
                    dim -= 1

            indexes.append(dim)
            
        # this is the already separated data
        for sepKey, val in data.iteritems():
            result = {}
            self._separate__(val, (), result, (), indexes)
            data[sepKey] = result
        
        return data
    
    def _sort(self, data):
        if 'sortBy' in self._configurator.visualization:
            sortBy = self._configurator.visualization['sortBy'].copy() #copy since we use popitem() to access the only expected item
            
            # REM: here we do hard coded stuff!!!
            assert type(sortBy) is dict
            assert len(sortBy) == 1, "At the moment only a single sortBy criterium is supported."
            key, val = sortBy.popitem()
            
            assert key == 'stats', "It is only implemented to sort for statistic properties ATM..."
            
            # TODO: fix this, I feel pain while writting this, lets hope it is
            #       fast enough... how often do i have calculated the StatProps for every single item now???
            def myCmp(x, y):
                if len(x[1]) == 0 or len(y[1]) == 0:
                    return cmp(x[1], y[1])
                
                statX = StatisticProperties(x[1], self._configurator.statistics['confidence_level'])
                statY = StatisticProperties(y[1], self._configurator.statistics['confidence_level'])
                #print val, statX.__dict__[val], statY.__dict__[val], cmp(statX.__dict__[val], statY.__dict__[val])
                return cmp(statY.__dict__[val], statX.__dict__[val])
                
            #REM: lazy... assert that we have actually used separateBy and groupBy already
            for separateFile, sepData in data.iteritems():
                assert type(separateFile) is tuple
                for group, groupData in sepData.items():
                    assert type(group) is tuple or type(group) is str, "Group is not a tuple or string: " + str(type(group)) + " " + str(group)
                    assert type(groupData) is dict
                    
                    groupData = self._flatten(groupData)
                    
                    #now the tuple with potential names and the data lists should be left
                    list = [(key, points) for key, points in groupData.iteritems()]
                    list = sorted(list, cmp=myCmp)
                    
                    sepData[group] = list
                    # REM: list can be unzipped later by: nameList, valList = zip(*list)
        
        return data

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

class ReporterOld:
    
    def __init__(self, config, output_file = None):
        self.config = config
        self.benchmark_results = None
        self.benchmark_data = None
        self.profile_data = None
        self.output_file = output_file
        
        if output_file:
            globalActivateLayer(log_to_file)
            self.header_written = False
            self.file = open(self.output_file, 'w+')
    
    def set_data(self, data):
        (result, benchmark_data) = data
        self.benchmark_results = result
        self.benchmark_data = benchmark_data

    def compile_report(self):
        pass

    @after(profile)
    def compile_report(self, __result__):
        memory_lines = []
        opcode_lines = []
        library_lines = []
        
        dict = profile_data[0].get_memory_usage()
        line = "ObjectSize:" + "\t".join(dict.keys())
        memory_lines.append(line)
        
        dict = profile_data[0].get_library_usage()
        line = "Library:" + "\t".join(dict.keys())
        library_lines.append(line)
        
        dict = profile_data[0].get_opcode_usage()
        line = "Opcodes:" + "\t".join(dict.keys())
        opcode_lines.append(line)
        
        for profile in profile_data:
            vm, bench = profile.get_vm_and_benchmark()
            head = "%s:%s"%(vm, bench)
            memory_lines.append(head + "\t".join(profile.get_memory_usage().values()))
            opcode_lines.append(head + "\t".join(profile.get_opcode_usage().values()))
            library_lines.append(head + "\t".join(profile.get_library_usage().values()))
            
        report = "\n".join(memory_lines)
        report = report + "\n"
        report = "\n".join(opcode_lines)
        report = report + "\n"
        report = "\n".join(library_lines)
        
        return report
            
    def normalize_data(self, profile_data):
        for profileA in profile_data:
            for profileB in profile_data:
                if profileA != profileB:
                    profileA.normalize(profileB)
                    
    def report_profile_results(self, verbose):
        profile_data = self.normalize_data(self.profile_data)
        report = self.compile_report(verbose)
        return report
    
    def report(self, data, current_vm, num_cores, input_size):
        pass
    
    @after(log_to_file)
    def report(self, data, current_vm, num_cores, input_size, __result__):
        if not self.header_written:
            self.file.write("VM\tCores\tInputSize\tBenchmark\tMean\tStdDev\tInterv_low\tInterv_high\tError\n")
            self.header_written = True
            
        for bench_name, values in data.iteritems():
            (mean, sdev, ((i_low, i_high), error), interval_t) = values
            line = "\t".join((current_vm, str(num_cores), str(input_size), bench_name, str(mean), str(sdev), str(i_low), str(i_high), str(error)))
            self.file.write(line + "\n")
            
        self.file.flush()
    
    def final_report(self, verbose):
        if self.profile_data:
            print self.report_profile_results(verbose)
        
        if self.benchmark_data:
            print self.report_benchmark_results(verbose)
        
    def old(self):
        if self.output_file is not None:
            if not verbose:
                if self.profile_data is not None:
                    profile = self.report_profile_results(True)
                benchmark = self.report_benchmark_results(True)
        
            f = open(self.output_file, 'w+')
            try:
                f.write(profile)
                f.write(benchmark)
            finally:
                f.close()
                
    
    def report_benchmark_results(self, verbose):
        report = "VM\tBenchmark\tMean\tStdDev\tInterv_low\tInterv_high\tError\n"
        lines = []
        for (vm, benchmarks) in self.benchmark_results.items():
            for (benchmark, results) in benchmarks.items():
                (mean, sdev, ((i_low, i_high), error),
                             interval_t) = results
                lines.append("\t".join([vm, benchmark, str(mean), str(sdev), str(i_low), str(i_high), str(error)]))
        
        report += "\n".join(lines)
        return report
