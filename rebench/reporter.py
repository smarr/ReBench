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
from __future__ import print_function
from datetime import datetime
import time
import logging
from .statistics import StatisticProperties
from .persistence import DataPointPersistence
import json
import urllib2
import urllib
import re
import locale

try:
    import matplotlib
    #check http://matplotlib.sourceforge.net/faq/installing_faq.html#what-is-a-backend for backends
    matplotlib.use('AGG') #PDF crashes with test.conf :(

    import numpy as np
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon
except ImportError:
    logging.info("matplotlib was not found, import failed: " + str(ImportError))


class Reporter:

    def runFailed(self, runId, cmdline, returncode, output):
        raise NotImplementedError('Subclass responsibility')
    
    def configurationCompleted(self, runId, statistics, cmdline):
        raise NotImplementedError('Subclass responsibility')
    
    def jobCompleted(self, configurations, dataAggregator):
        raise NotImplementedError('Subclass responsibility')
    
    def setTotalNumberOfConfigurations(self, numConfigs):
        raise NotImplementedError('Subclass responsibility')
    
    def startConfiguration(self, runId):
        raise NotImplementedError('Subclass responsibility')
    
class Reporters(Reporter):
    """Distributes the information to all registered reporters."""
    
    def __init__(self, reporters):
        if type(reporters) is list:
            self._reporters = reporters
        else:
            self._reporters = [reporters]

    def runFailed(self, runId, cmdline, returncode, output):
        for reporter in self._reporters:
            reporter.runFailed(runId, cmdline, returncode, output)
            
    def configurationCompleted(self, runId, statistics, cmdline):
        for reporter in self._reporters:
            reporter.configurationCompleted(runId, statistics, cmdline)
    
    def jobCompleted(self, configurations, dataAggregator):
        for reporter in self._reporters:
            reporter.jobCompleted(configurations, dataAggregator)
    
    def setTotalNumberOfConfigurations(self, numConfigs):
        for reporter in self._reporters:
            reporter.setTotalNumberOfConfigurations(numConfigs)
    
    def startConfiguration(self, runId):
        for reporter in self._reporters:
            reporter.startConfiguration(runId)

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
    
    def _path_to_string(self, path):
        out = []
        out.append(path[0].as_simple_string())
        for item in path[1:]:
            if item:
                out.append(str(item))
        return " ".join(out) + " "
    
    def _generate_all_output(self, data, path):
        assert type(data) is dict or type(data) is list
        
        if type(data) is dict:
            for key, val in data.iteritems():
                for result in self._generate_all_output(val, path + (key,)):
                    yield result
        else:
            stats = StatisticProperties(data, 
                                        self._configurator.reporting['confidence_level'])
                
            out = [ self._path_to_string(path) ]
            
            self._output_stats(out, stats)
            
            result = "".join(out)
            yield result

class CliReporter(TextReporter):
    """ Reports to standard out using the logging framework """
    
    def __init__(self, configurator):
        TextReporter.__init__(self, configurator)
        self._numConfigs    = None
        self._runsCompleted = 0
        self._startTime     = None
        self._runsRemaining = 0
        
        # TODO: readd support, think, we need that based on the proper config, i.e., the run id
#         self._min_runtime = configurator.statistics.min_runtime

    def runFailed(self, runId, cmdline, returncode, output):
        # Additional information in debug mode
        result = []
        result.append("[%s] Run failed: " % datetime.now())
        result += self._configuration_details(runId) 
        result.append("\n")
        result = "".join(result)
        logging.debug(result)
        
        # Standard error output
        if returncode == -9:
            log_msg = "Run timed out. returncode: %s"
        else:
            log_msg = "Run failed returncode: %s"
        
        print(log_msg % returncode)
        
        print("Cmd: %s\n" % cmdline)
        
        if 'max_runtime' in runId.cfg.suite:
            logging.debug("max_runtime: %s" % (runId.cfg.suite['max_runtime']))
        logging.debug("cwd: %s" % (runId.cfg.suite['location']))
        
        if len(output.strip()) > 0:
            print("Output:\n%s\n" % output)    

    def configurationCompleted(self, runId, statistics, cmdline):
        result = []
        result.append("[%s] Configuration completed: " % datetime.now())
        
        result += self._configuration_details(runId, statistics) 
            
        result.append("\n")
        
        result = "".join(result)
        
        logging.debug(result)
        
        self._runsCompleted += 1
        self._runsRemaining -= 1

        # TODO: readd warning for min_runtime        
#         if self._min_runtime:
#             if statistics.mean < self._min_runtime:
#                 print("WARNING: measured mean is smaller than min_runtime (%s) \t mean: %.1f [%.1f, %.1f]\trun id: %s"
#                       % (self._min_runtime,
#                          statistics.mean, statistics.confIntervalLow,
#                          statistics.confIntervalHigh, runId.as_simple_string())) 
#                 print("Cmd: %s" % cmdline)
#         
#         self._configurator.statistics.min_runtime

    def jobCompleted(self, configurations, dataAggregator):
        print("[%s] Job completed" % datetime.now())
        for line in self._generate_all_output(dataAggregator.getData(), ()):
            print(line)
    
    def setTotalNumberOfConfigurations(self, numConfigs):
        self._numConfigs = numConfigs
        self._runsRemaining = numConfigs
    
    def startConfiguration(self, runId):
        
        
        if self._runsCompleted > 0:
            current = time.time()
            
            etl = (current - self._startTime) / self._runsCompleted * self._runsRemaining
            sec = etl % 60
            m   = (etl - sec) / 60 % 60
            h   = (etl - sec - m) / 60 / 60
            print("Run %s \t configurations left: %00d \t estimated time left: %02d:%02d:%02d"%(runId.cfg.name, self._runsRemaining, round(h), round(m), round(sec)))
        else:
            self._startTime = time.time()
            print("Run %s \t configurations left: %d" % (runId.cfg.name, self._runsRemaining))
            
    def _output_stats(self, outputList, statistics):
        if not statistics:
            return
        
        if statistics.failedRun:
            outputList.append("run failed.")
        else:
            outputList.append("\tmean: %.1f [%.1f, %.1f]" % (statistics.mean,
                                                             statistics.confIntervalLow,
                                                             statistics.confIntervalHigh))
    

class FileReporter(TextReporter):
    """ should be mainly a log file
        data is the responsibility of the DataAggregator
    """
    
    def __init__(self, fileName, configurator):
        TextReporter.__init__(self, configurator)
        self._file = open(fileName, 'a+')

    def runFailed(self, runId, cmdline, returncode, output):
        result = []
        result.append("[%s] Run failed: " % datetime.now())

        result += self._configuration_details(runId) 

        result.append("\n")

        self._file.writelines(result)
        
    def configurationCompleted(self, runId, statistics, cmdline):
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
    
    def setTotalNumberOfConfigurations(self, numConfigs):
        pass
    
    def startConfiguration(self, runId):
        pass

            
class CSVFileReporter(Reporter):
    """ Will generate a CSV file for processing in another program as for instance Excel or Numbers """
    
    def __init__(self, configurator):
        self._file = open(configurator.reporting['csv_file'], 'a+')
        self._configurator = configurator
    
    def runFailed(self, runId, cmdline, returncode, output):
        pass
    
    def configurationCompleted(self, runId, statistics, cmdline):
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
                            self._configurator.reporting['confidence_level']).as_tuple()) # now add the actual result data
            table.append(row)
        
        for row in table:
            self._file.write(";".join([i if type(i) == str else locale.format("%f", i or 0.0) for i in row]) + "\n")
            
        self._file.close()
        locale.setlocale(locale.LC_ALL, old_locale)
    
    def setTotalNumberOfConfigurations(self, numConfigs):
        pass
    
    def startConfiguration(self, runId):
        pass
        

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
        
        if "project" not in self._codespeed_cfg and self._configurator.options.project is None:
            raise ValueError("The config file needs to configure a 'project' in the reporting.codespeed section, or --project has to be given on the command line.")
        
        if "url" not in self._codespeed_cfg:
            raise ValueError("The config file needs to configure a URL to codespeed in the reporting.codespeed section")

        
        # contains the indexes into the data tuples for
        # the parameters
        self._indexMap = DataPointPersistence.data_mapping()
        
    def runFailed(self, runId, cmdline, returncode, output):
        pass


    def configurationCompleted(self, runId, statistics, cmdline):
        if not self._incremental_report:
            return
        
        # if self._incremental_report is true we are going to talk to codespeed immediately
        results = [self._formatForCodespeed(runId, statistics)]
        
        # now, send them of to codespeed
        self._sendToCodespeed(results)
    
    def _result_data_template(self):
        if self._configurator.options.project:
            project = self._configurator.options.project
        else:
            project = self._codespeed_cfg['project']
        
        # all None values have to be filled in
        return {
            'commitid':     self._configurator.options.commit_id,
            'project':      project,
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

    def _formatForCodespeed(self, runId, stats = None):
        run = runId.as_tuple()
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
        
        if 'codespeed_name' in runId.cfg.additional_config:
            name = runId.cfg.additional_config['codespeed_name']
        else:
            name = self._beautifyBenchmarkName(run[self._indexMap['bench']]) + " (%(cores)s cores, %(input_sizes)s %(extra_args)s)"

        name = name % {'cores' : run[self._indexMap['cores']]             or "",
                       'input_sizes' : run[self._indexMap['input_sizes']] or "",
                       'extra_args'  : run[self._indexMap['extra_args']]  or ""}
        
        result['benchmark'] = name
        
        return result

    def _prepareResult(self, run, measures):
        if measures:
            # get the statistics
            stats = StatisticProperties(measures, self._configurator.reporting['confidence_level'])
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
    
    def setTotalNumberOfConfigurations(self, numConfigs):
        pass
    
    def startConfiguration(self, runId):
        pass
    

class DiagramResultReporter(Reporter):
    
    def __init__(self, configurator):
        self._configurator = configurator
        self._separateByMapping = DataPointPersistence.data_mapping()
        self._separateByIndexes = None

    def runFailed(self, runId, cmdline, returncode, output):
        pass

    
    def configurationCompleted(self, runId, statistics, cmdline):
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
                
                statX = StatisticProperties(x[1], self._configurator.reporting['confidence_level'])
                statY = StatisticProperties(y[1], self._configurator.reporting['confidence_level'])
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

