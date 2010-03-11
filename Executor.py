# Copyright (c) 2009 Stefan Marr <http://www.stefan-marr.de/>
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

import logging
import subprocess
import os
import time
from Statistics import StatisticProperties

from contextpy import layer, activelayers, after,before
# proceed, activelayer, around, base, globalActivateLayer, globalDeactivateLayer

benchmark = layer("benchmark")
profile = layer("profile")
quick   = layer("quick")

class Executor:
    
    def __init__(self, configurator, dataAggregator, reporter = None):
        self._configurator = configurator
        self._data = dataAggregator
        self._reporter = reporter
        self._jobs = [] # the list of configurations to be executed
                
    def _construct_cmdline(self, bench_cfg, perf_reader, cores, input_size, variable):
        cmdline  = ""
        cmdline += "cd %s && "%(bench_cfg.suite['location'])
        
        if 'ulimit' in bench_cfg.suite:
            cmdline += "ulimit -t %s && "%(bench_cfg.suite['ulimit'])
                
        if self._configurator.options.use_nice:
            cmdline += "sudo nice -n-20 "
        
        vm_cmd = "%s/%s %s" % (os.path.abspath(bench_cfg.vm['path']),
                               bench_cfg.vm['binary'],
                               bench_cfg.vm.get('args', ""))
            
        vm_cmd = perf_reader.acquire_command(vm_cmd)
            
        cmdline += vm_cmd 
        cmdline += bench_cfg.suite['command']
        
        cmdline = cmdline % {'benchmark':bench_cfg.name, 'input':input_size, 'variable':variable, 'cores' : cores}
        
        if bench_cfg.extra_args is not None:
            cmdline += " %s" % (bench_cfg.extra_args or "")
        
        return cmdline
    
    def _exec_configuration(self, cfg, cores, input_size, var_val):
        runId = (cfg, cores, input_size, var_val)
        
        perf_reader = self._get_performance_reader_instance(cfg.performance_reader)
        
        cmdline = self._construct_cmdline(cfg,
                                          perf_reader,
                                          cores,
                                          input_size,
                                          var_val)
        
        logging.debug("command = " + cmdline)
        
        #error = (consequent_erroneous_runs, erroneous_runs)    
        terminate, error = self._check_termination_condition(runId, (0, 0))
        while not terminate:
            terminate, error = self._generate_data_point(cmdline, error, perf_reader, runId)
            logging.debug("Run: #%d"%(self._data.getNumberOfDataPoints(runId)))

        
        #TODO: add here some user-interface stuff to show progress
    
        #self._reporter.report(self.result[self.current_vm][self.num_cores][input_size],
        #                      self.current_vm, self.num_cores, input_size)
        
        #TODO: logging.debug("Run completed for %s:%s (size: %s, cores: %d), mean=%f, sdev=%f"%(self.current_vm, bench_name, input_size, self.num_cores, mean, sdev))
    
    def _get_performance_reader_instance(self, reader):
        p = __import__("performance", fromlist=reader)
        return getattr(p, reader)()

    @before(benchmark)
    def _exec_vm_run(self, input_size):
        logging.debug("Statistic cfg: min_runs=%s, max_runs=%s"%(self.config["statistics"]["min_runs"],
                                                                 self.config["statistics"]["max_runs"]))
        
        
    def _generate_data_point(self, cmdline, error, perf_reader, runId):
        p = subprocess.Popen(cmdline, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        (output, _) = p.communicate()
        
        (cnf, _, _, _) = runId
        if p.returncode != 0:
            (consequent_erroneous_runs, erroneous_runs) = error
            
            consequent_erroneous_runs += 1
            erroneous_runs += 1
            logging.warning("Run #%d of %s:%s failed"%(self._data.getNumberOfDataPoints(runId),
                                                       cnf.vm['name'], cnf.name))
            error = (consequent_erroneous_runs, erroneous_runs)
        else:
            logging.debug(u"Output: %s"%(output))
            error = self._eval_output(output, runId, perf_reader, error)
        
        return self._check_termination_condition(runId, error)
    
    def _eval_output(self, output, runId, perf_reader, error):
        return error
    
    @after(benchmark)
    def _eval_output(self, output, runId, perf_reader, error, __result__):
        (cfg, _, _, _) = runId
        consequent_erroneous_runs, erroneous_runs = error
        
        try:
            (total, dataPoints) = perf_reader.parse_data(output)
            #self.benchmark_data[self.current_vm][self.current_benchmark].append(exec_time)
            self._data.addDataPoints(runId, dataPoints)
            consequent_erroneous_runs = 0
            logging.debug("Run %s:%s result=%s"%(cfg.vm['name'], cfg.name, total))
            
        except RuntimeError:
            consequent_erroneous_runs += 1
            erroneous_runs += 1
            logging.warning("Run of %s:%s failed"%(cfg.vm['name'], cfg.name))
            
        return consequent_erroneous_runs, erroneous_runs
        
        
    def _check_termination_condition(self, runId, error):
        return False, error
    
    @after(profile)
    def _check_termination_condition(self, runId, error, __result__):
        return True, error
    
    @after(benchmark)
    def _check_termination_condition(self, runId, error, __result__):
        terminate, (consequent_erroneous_runs, erroneous_runs) = __result__
        
        numDataPoints = self._data.getNumberOfDataPoints(runId)
        (cfg, _, _, _) = runId
        
        if consequent_erroneous_runs >= 3:
            logging.error("Three runs of %s have failed in a row, benchmark is aborted"%(cfg.name))
            terminate = True
        elif erroneous_runs > numDataPoints / 2 and erroneous_runs > 6:
            logging.error("Many runs of %s are failing, benchmark is aborted."%(cfg.name))
            terminate = True
        elif numDataPoints >= self._configurator.statistics["max_runs"]:
            logging.debug("Reached max_runs for %s"%(cfg.name))
            terminate = True
        elif (numDataPoints >= self._configurator.statistics["min_runs"]
              and self._confidence_reached(runId)):
            logging.debug("Confidence is reached for %s"%(cfg.name))
            terminate = True
        
        return terminate, (consequent_erroneous_runs, erroneous_runs)
    
    @after(quick)
    def _check_termination_condition(self, runId, error, __result__):
        terminate, error = __result__
        
        (cfg, _, _, _) = runId
        
        if len(self.current_data) >= self.config["quick_runs"]["max_runs"]:
            logging.debug("Reached max_runs for %s"%(cfg.name))
            terminate = True
        elif (len(self.current_data) > self.config["quick_runs"]["min_runs"]
              and sum(self.current_data)  / (1000 * 1000) > self.config["quick_runs"]["max_time"]):
            logging.debug("Maximum runtime is reached for %s"%(cfg.name))
            terminate = True
        
        return terminate, error
   
                
    def _confidence_reached(self, runId):
        
        stats = StatisticProperties(self._data.getDataSet(runId),
                                    self._configurator.statistics['confidence_level'])
        
        
        
        logging.debug("Run: %d, Mean: %f, current error: %f, Interval: [%f, %f]"%(
                      stats.numSamples, stats.mean,
                      stats.confIntervalSize, stats.confIntervalLow, stats.confIntervalHigh))
        
        if stats.confIntervalSize < self._configurator.statistics["error_margin"]:
            return True
        else:
            return False
    
    def _generate_all_configs(self, benchConfigs):
        result = []
        
        for cfg in benchConfigs:
            for cores  in cfg.vm['cores']:
                for input_size in cfg.suite['input_sizes']:
                    for var_val in cfg.suite['variable_values']:
                        result.append((cfg, cores, input_size, var_val))
        
        return result
    
    def execute(self):
        startTime = None
        runsCompleted = 0
        (actions, benchConfigs) = self._configurator.getBenchmarkConfigurations()
        configs = self._generate_all_configs(benchConfigs)
        
        runsRemaining = len(configs)
        
        for action in actions:
            with activelayers(layer(action)):
                for (cfg, cores, input_size, var_val) in configs:
                    self._reporter.info("Configurations left: %d"%(runsRemaining))
                    
                    if runsCompleted > 0:
                        current = time.time()
                        
                        etl = (current - startTime) / runsCompleted * runsRemaining
                        sec = etl % 60
                        min = (etl - sec) / 60 % 60
                        h   = (etl - sec - min) / 60 / 60
                        self._reporter.info("Estimated time left: %02d:%02d:%02d"%(round(h), round(min), round(sec)))
                    else:
                        startTime = time.time()
                    
                    self._exec_configuration(cfg, cores, input_size, var_val)
                    
                    runsCompleted = runsCompleted + 1
