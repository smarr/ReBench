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
import math
import numpy
import time
import scipy.stats as stats
import scipy.stats.distributions as distributions

from contextpy import layer, proceed, activelayer, activelayers, after, around, before, base, globalActivateLayer, globalDeactivateLayer

benchmark = layer("benchmark")
profile = layer("profile")
quick   = layer("quick")

class Executor:
    
    def __init__(self, config, description, actions, executions,
                 benchmark=None, input_size=None):
        self.desctiption = description
        self.actions = actions
        self.executions = executions
        self.input_size = input_size
        self.config = config
        self.result = {}
        self.benchmark_data = {}
        self.current_data = None
        self.current_vm = None
        self.current_benchmark_suite = config["benchmark-suites"][benchmark]
        self.current_benchmark = None
        
        self.perf_reader = None
        self.start_time = time.clock()
        
        self.num_cores = 1
        
        self.reporter = None
        
    def set_reporter(self, reporter):
        self.reporter = reporter
        
    def _construct_cmdline(self, command, input_size, benchmark, ulimit,
                           bench_location, path, binary, vm_args, perf_reader, extra_args):
        cmdline  = ""
        cmdline += "cd %s && "%(bench_location)
        
        if ulimit:
            cmdline += "ulimit -t %s && "%(ulimit)
                
        if self.config["options"]["use_nice"]:
            cmdline += "sudo nice -n-20 "
        
        vm_cmd = "%s/%s %s"%(path, binary, (vm_args or "")%(dict(cores=self.num_cores)))
            
        if perf_reader:
            vm_cmd = perf_reader.acquire_command(vm_cmd)
            
        cmdline += vm_cmd 
        cmdline += command%(dict(benchmark=benchmark, input=input_size))
        if extra_args is not None:
            cmdline += " %s"%(extra_args or "")
        return cmdline
    
    def _exec_vm_run(self, input_size):
        self.result[self.current_vm] = {}
        self.result[self.current_vm][self.num_cores] = {}
        self.result[self.current_vm][self.num_cores][input_size] = {}
        self.benchmark_data[self.current_vm] = {}
        vm_cfg = self.config["virtual_machines"][self.current_vm]
        

        # some VMs have there own versions of the benchmarks
        if self.current_benchmark_suite.has_key("location"):
            bench_location = self.current_benchmark_suite["location"]
        else:
            bench_location = vm_cfg["path"]
        
        for bench in self.current_benchmark_suite["benchmarks"]:
            if type(bench) == dict:
                bench_name = bench.keys()[0]
                extra_args = str(bench[bench_name].get('extra-args', ""))
                perf_reader= bench[bench_name].get('performance_reader', None)
                if perf_reader:
                    perf_reader = self._get_performance_reader_instance(perf_reader)
            else:
                extra_args = None
                bench_name = bench
                perf_reader = None
            
            self.current_benchmark = bench_name
            
            self.current_data = []
            self.benchmark_data[self.current_vm][bench_name] = self.current_data
            
            if not perf_reader:
                perf_reader = self.perf_reader
            
            cmdline = self._construct_cmdline(self.current_benchmark_suite["command"],
                                              input_size,
                                              bench_name,
                                              self.current_benchmark_suite.get("ulimit", None),
                                              bench_location, 
                                              vm_cfg["path"], 
                                              vm_cfg["binary"],
                                              vm_cfg.get("args", None),
                                              perf_reader,
                                              extra_args)
            logging.debug("command = " + cmdline)
            
            terminate = False
            error = (0, 0)  # (consequent_erroneous_runs, erroneous_runs)
            
            while not terminate:
                terminate, error = self._exec_benchmark_run(cmdline, error, perf_reader)
                logging.debug("Run: #%d"%(len(self.current_data)))
                    
            self._consolidate_result(bench_name, input_size)
            
            
            # TODO add here some user-interface stuff to show progress
        
        if self.reporter:
            self.reporter.report(self.result[self.current_vm][self.num_cores][input_size],
                                 self.current_vm, self.num_cores, input_size)
        
        
        
    def _consolidate_result(self, bench_name, input_size):
        results = {}
        
        for run in self.current_data:
            for result in run[1]:
                bench = result['bench'] + "-" + result.get('subCriterion', "")
                values = results.get(bench, [])
                values.append(result['time'])
                results[bench] = values
        
        for bench_name, values in results.iteritems():
            result = self._confidence(values, 
                                      self.config["statistics"]['confidence_level'])
            self.result[self.current_vm][self.num_cores][input_size][bench_name] = result
            
            (mean, sdev, interval_details, interval_details_t) = result 
            logging.debug("Run completed for %s:%s (size: %s, cores: %d), mean=%f, sdev=%f"%(self.current_vm, bench_name, input_size, self.num_cores, mean, sdev))
    
    def _get_performance_reader_instance(self, reader):
        p = __import__("performance", fromlist=reader)
        return getattr(p, reader)()

    @before(benchmark)
    def _exec_vm_run(self, input_size):
        logging.debug("Statistic cfg: min_runs=%s, max_runs=%s"%(self.config["statistics"]["min_runs"],
                                                                 self.config["statistics"]["max_runs"]))
        
        self.perf_reader = self._get_performance_reader_instance(self.current_benchmark_suite["performance_reader"])
        
    def _exec_benchmark_run(self, cmdline, error, perf_reader):
        (consequent_erroneous_runs, erroneous_runs) = error
        p = subprocess.Popen(cmdline, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        (output, tmp) = p.communicate()
        
        if p.returncode != 0:
            consequent_erroneous_runs += 1
            erroneous_runs += 1
            logging.warning("Run #%d of %s:%s failed"%(len(self.current_data), self.current_vm, self.current_benchmark))
        else:
            logging.debug(u"Output: %s"%(output))
            self._eval_output(output, perf_reader, consequent_erroneous_runs, erroneous_runs)
        
        return self._check_termination_condition(consequent_erroneous_runs, erroneous_runs)
    
    def _eval_output(self, output, perf_reader, consequent_erroneous_runs, erroneous_runs):
        pass
    
    @after(benchmark)
    def _eval_output(self, output, perf_reader, consequent_erroneous_runs, erroneous_runs, __result__):
        exec_time = perf_reader.parse_data(output)
        if exec_time[0] is None:
            consequent_erroneous_runs += 1
            erroneous_runs += 1
            logging.warning("Run of %s:%s failed"%(self.current_vm, self.current_benchmark))
        else:    
            #self.benchmark_data[self.current_vm][self.current_benchmark].append(exec_time)
            self.current_data.append(exec_time)
            consequent_erroneous_runs = 0
            logging.debug("Run %s:%s result=%s"%(self.current_vm, self.current_benchmark, exec_time[0]))
        
    def _check_termination_condition(self, consequent_erroneous_runs, erroneous_runs):
        return False, (consequent_erroneous_runs, erroneous_runs)
    
    @after(profile)
    def _check_termination_condition(self, consequent_erroneous_runs, erroneous_runs, __result__):
        return True, (consequent_erroneous_runs, erroneous_runs)
    
    @after(benchmark)
    def _check_termination_condition(self, consequent_erroneous_runs, erroneous_runs, __result__):
        terminate, (consequent_erroneous_runs, erroneous_runs) = __result__
        
        if consequent_erroneous_runs >= 3:
            logging.error("Three runs of %s have failed in a row, benchmark is aborted"%(self.current_benchmark))
            terminate = True
        elif erroneous_runs > len(self.current_data) / 2 and erroneous_runs > 6:
            logging.error("Many runs of %s are failing, benchmark is aborted."%(self.current_benchmark))
            terminate = True
        elif len(self.current_data) >= self.config["statistics"]["max_runs"]:
            logging.debug("Reached max_runs for %s"%(self.current_benchmark))
            terminate = True
        elif (len(self.current_data) >= self.config["statistics"]["min_runs"]
              and self._confidence_reached([val[0] for val in self.current_data])):
            logging.debug("Confidence is reached for %s"%(self.current_benchmark))
            terminate = True
        
        return terminate, (consequent_erroneous_runs, erroneous_runs)
    
    @after(quick)
    def _check_termination_condition(self, consequent_erroneous_runs, erroneous_runs, __result__):
        terminate, (consequent_erroneous_runs, erroneous_runs) = __result__
        
        if len(self.current_data) >= self.config["quick_runs"]["max_runs"]:
            logging.debug("Reached max_runs for %s"%(self.current_benchmark))
            terminate = True
        elif (len(self.current_data) > self.config["quick_runs"]["min_runs"]
              and sum(self.current_data)  / (1000 * 1000) > self.config["quick_runs"]["max_time"]):
            logging.debug("Maximum runtime is reached for %s"%(self.current_benchmark))
            terminate = True
        
        return terminate, (consequent_erroneous_runs, erroneous_runs)
   
                
    def _confidence_reached(self, values):
        (mean, sdev, norm_dist, t_dist) = \
            self._confidence(values, self.config["statistics"]['confidence_level'])
        ((i_low, i_high), i_percentage) = norm_dist
        
        logging.debug("Run: %d, Mean: %f, current error: %f, Interval: [%f, %f]"%(
                            len(values), mean, i_percentage, i_low, i_high))
        
        if i_percentage < self.config["statistics"]["error_margin"]:
            return True
        else:
            return False
        
    def _confidence(self, samples, confidence_level):
        """This function determines the confidence interval for a given set of samples, 
           as well as the mean, the standard deviation, and the size of the confidence 
           interval as a percentage of the mean.
        """
        
        mean = numpy.mean(samples)
        sdev = numpy.std(samples)
        n    = len(samples)
        norm = distributions.norm.ppf((1 + confidence_level)/2.0)
        
        
        interval_low  = mean - (norm * sdev / math.sqrt(n))
        interval_high = mean + (norm * sdev / math.sqrt(n))
        interval = (interval_low, interval_high)
        
        # original calculations from javastats, using students i.e. t distribution for fewer values
        df   = n - 1
        t    = distributions.t.ppf((1 + confidence_level)/2.0, df)
        interval_t = (interval_low_t, interval_high_t) = ( mean - t * sdev / math.sqrt(n) , mean + t * sdev / math.sqrt(n) )
        
        interval_size = interval_high - interval_low
        interval_percentage = interval_size / mean
        return (mean, sdev,
                (interval, interval_percentage), 
                (interval_t, (interval_high_t - interval_low_t) / mean)) 
    
    def execute(self):
        startTime = None
        runsCompleted = 0
        
        if isinstance(self.actions, basestring):
            self.actions = [self.actions]
                
        for action in self.actions:
            with activelayers(layer(action)):
                for vm in self.executions:
                    self.current_vm = vm
                    cur_vm = self.config["virtual_machines"][self.current_vm]
                    cores = cur_vm["cores"] or [1]
                    
                    if self.input_size is None:
                        self.input_size = self.current_benchmark_suite["input_sizes"]
                        
                    for num_cores in cores:
                        self.num_cores = num_cores
                        
                        if not isinstance(self.input_size, list):
                            self.input_size = [self.input_size]
                            
                        for input_size in self.input_size:
                            totalRuns = len(self.executions) * len(cores) * len(self.input_size)
                            print "Runs left: %d"%( totalRuns - runsCompleted )
                            
                            if runsCompleted > 0:
                                current = time.time()
                                
                                etl = (current - startTime) / runsCompleted * ( totalRuns - runsCompleted )
                                sec = etl % 60
                                min = (etl - sec) / 60 % 60
                                h   = (etl - sec - min) / 60 / 60
                                print "Estimated time left: %02d:%02d:%02d"%(round(h), round(min), round(sec))
                            else:
                                startTime = time.time()
                            
                            self._exec_vm_run(input_size)
                            
                            runsCompleted = runsCompleted + 1
                            
    
    def get_results(self):
        return (self.result, self.benchmark_data)
    
        