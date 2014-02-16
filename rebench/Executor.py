# Copyright (c) 2009-2014 Stefan Marr <http://www.stefan-marr.de/>
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
import subprocess_with_timeout as subprocess_timeout

from .statistics  import StatisticProperties
from .performance import OutputNotParseable

class Executor:
    
    def __init__(self, runs, use_nice, data_aggregator, reporter = None):
        self._runs     = runs
        self._use_nice = use_nice
        self._data     = data_aggregator
        self._reporter = reporter
    
    def _construct_cmdline(self, run_id, perf_reader):
        cmdline  = ""
                
        if self._use_nice:
            cmdline += "nice -n-20 "
        
        cmdline += perf_reader.acquire_command(run_id.cmdline())
                
        return cmdline
    
    def _exec_configuration(self, run_id):
        termination_check = run_id.create_termination_check()
        
        run_id.run_config.log()
        
        self._reporter.startConfiguration(run_id)
        
        perf_reader = self._get_performance_reader_instance(run_id.bench_cfg.performance_reader)
        
        cmdline = self._construct_cmdline(run_id, perf_reader)
        
        #error = (consequent_erroneous_runs, erroneous_runs)    
        terminate, error = self._check_termination_condition(run_id, (0, 0), termination_check)
        stats = StatisticProperties(run_id.get_data_points(),
                                    run_id.requested_confidence_level)
        
        # now start the actual execution
        while not terminate:
            terminate, error = self._generate_data_point(cmdline, error, perf_reader, run_id, termination_check)
            
            stats = StatisticProperties(run_id.get_total_values(),
                                        run_id.requested_confidence_level)
            
            logging.debug("Run: #%d"%(stats.num_samples))

        self._reporter.configurationCompleted(run_id, stats, cmdline)
        
    def _get_performance_reader_instance(self, reader):
        # depending on how ReBench was executed, the name might one of the two 
        try:
            p = __import__("rebench.performance", fromlist=reader)
        except ImportError:
            p = __import__("performance", fromlist=reader)
        
        return getattr(p, reader)()
        
    def _generate_data_point(self, cmdline, error, perf_reader, run_id, termination_check):
        # execute the external program here
        (returncode, output, _) = subprocess_timeout.run(cmdline, cwd=run_id.bench_cfg.suite.location,
                                                         stdout=subprocess.PIPE,
                                                         stderr=subprocess.STDOUT,
                                                         shell=True, timeout=run_id.bench_cfg.suite.max_runtime)
        
        if returncode != 0:
            (consequent_erroneous_runs, erroneous_runs) = error
            
            consequent_erroneous_runs += 1
            erroneous_runs += 1
            
            error = (consequent_erroneous_runs, erroneous_runs)
            self._reporter.runFailed(run_id, cmdline, returncode, output)
        else:
            error = self._eval_output(output, run_id, perf_reader, error, cmdline)
        
        return self._check_termination_condition(run_id, error, termination_check)
    
    def _eval_output(self, output, run_id, perf_reader, error, cmdline):
        consequent_erroneous_runs, erroneous_runs = error
        
        try:
            data_points = perf_reader.parse_data(output, run_id)
            
            for data_point in data_points:
                run_id.add_data_point(data_point)
                self._data.persist_data_point(data_point)
                logging.debug("Run %s:%s result=%s"%(run_id.bench_cfg.vm.name, run_id.bench_cfg.name, data_point.get_total_value()))
            
            consequent_erroneous_runs = 0
        except OutputNotParseable as parse_error:
            consequent_erroneous_runs += 1
            erroneous_runs += 1
            self._reporter.runFailed(run_id, cmdline, 0, output)
            
        return consequent_erroneous_runs, erroneous_runs

    def _check_termination_condition(self, run_id, error, termination_check):
        terminate = False
        consequent_erroneous_runs, erroneous_runs = error

        num_data_points = run_id.get_number_of_data_points()

        if termination_check.should_terminate(num_data_points):
            terminate = True
        elif consequent_erroneous_runs >= 3:
            logging.error("Three runs of %s have failed in a row, benchmark is aborted"%(run_id.bench_cfg.name))
            terminate = True
        elif erroneous_runs > num_data_points / 2 and erroneous_runs > 6:
            logging.error("Many runs of %s are failing, benchmark is aborted."%(run_id.bench_cfg.name))
            terminate = True
        
        return terminate, error
    
    def execute(self):
        self._reporter.setTotalNumberOfConfigurations(len(self._runs))
        
        for run_id in self._runs:
            self._exec_configuration(run_id)
                    
        self._reporter.jobCompleted(self._runs, self._data)
