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
from contextpy import layer, after, globalActivateLayer
# proceed, activelayer, activelayers, around, before, base,

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

    def configurationCompleted(self, runId, statistics):
        for reporter in self._reporters:
            reporter.configurationCompleted(runId, statistics)
    
    def jobCompleted(self, configurations, dataAggregator):
        for reporter in self._reporters:
            reporter.jobCompleted(configurations, dataAggregator)

class TextReporter(Reporter):
    
    def _configuration_details(self, runId, statistics):
        result = []
        
        criteria = (runId.cfg, ) + runId.variables + (runId.criterion, )
        
        for criterion in criteria:
            result.append(" %s" % criterion)
            
        result.append(" = ")
        
        for field, value in statistics.__dict__.iteritems():
            if not field.startswith('_'):
                result.append("%s: %s " % (field, value))
            
        return result

class CliReporter(TextReporter):
    """ Reports to standard out using the logging framework """
    
    def configurationCompleted(self, runId, statistics):
        result = []
        result.append("[%s] Configuration completed: " % datetime.now())
        
        result += self._configuration_details(runId, statistics) 
            
        result.append("\n")
        
        result = "".join(result)
        
        logging.debug(result)

    def jobCompleted(self, configurations, dataAggregator):
        #TODO: here we have to report all generated criteria/benchmarks values
        #      this is not done by the configurationCompleted, which is only reporting total criteria
        pass

class FileReporter(TextReporter):
    """ should be mainly a log file
        data is the responsibility of the DataAggregator
    """
    
    def __init__(self, fileName):
        self._file = open(fileName, 'a+')
        
    def configurationCompleted(self, runId, statistics):
        result = []
        result.append("[%s] Configuration completed: " % datetime.now())
        
        result += self._configuration_details(runId, statistics) 
            
        result.append("\n")
        
        self._file.writelines(result)
    
    def jobCompleted(self, configurations, dataAggregator):
        #TODO: here we have to report all generated criteria/benchmarks values
        #      this is not done by the configurationCompleted, which is only reporting total criteria
        pass

class ResultReporter(Reporter):
    pass

class DiagramResultReporter(Reporter):
    pass


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
