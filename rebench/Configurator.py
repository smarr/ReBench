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

import sys
import yaml
import logging
import traceback
from model.benchmark_config import BenchmarkConfig
from model.runs_config      import RunsConfig, QuickRunsConfig
from model.experiment       import Experiment 

from copy import deepcopy

def dict_merge_recursively(a, b):
    """Merges two dicts recursively.
       Both initial dicts remain unchanged."""
    
    if not isinstance(b, dict):
        return deepcopy(b)
    
    result = deepcopy(a)
    
    for k, v in b.iteritems():
        if k in result:
            result[k] = dict_merge_recursively(result[k], v)
        else:
            result[k] = deepcopy(v)
    
    return result


class Configurator:
    
    
    def __init__(self, fileName, cliOptions, expName = None):
        self._load_config(fileName)
        self._process_cli_options(cliOptions)
        self._exp_name  = expName
        
        self.runs       = RunsConfig(     **self._rawConfig.get(      'runs', {}))
        self.quick_runs = QuickRunsConfig(**self._rawConfig.get('quick_runs', {}))
        
        self._experiments = self._compile_experiments()
        
        self.visualization = self._rawConfig['experiments'][self.experiment_name()].get('visualization', None)
    def __getattr__(self, name):
        return self._rawConfig.get(name, None)
    
    def _load_config(self, file_name):
        try:
            f = file(file_name, 'r')
            self._rawConfig = yaml.load(f)
        except IOError:
            logging.error("There was an error opening the config file (%s)."%(file_name))
            logging.error(traceback.format_exc(0))
            sys.exit(-1)
        except yaml.YAMLError:
            logging.error("Failed parsing the config file (%s)."%(file_name))
            logging.error(traceback.format_exc(0))
            sys.exit(-1)
            
    def _process_cli_options(self, options):
        if options is None:
            return
        
        if options.debug:
            logging.basicConfig(level=logging.DEBUG)
            logging.getLogger().setLevel(logging.DEBUG)
            logging.debug("Enabled debug output.")
        else:
            logging.basicConfig(level=logging.ERROR)
            logging.getLogger().setLevel(logging.ERROR)
                    
        self.options = options
        
    def experiment_name(self):
        return self._exp_name or self.standard_experiment
    
    def data_file_name(self):
        """@TODO: might add a command-line option 'ff' is just a placeholder here..."""
        
        data_file = self._rawConfig['experiments'][self.experiment_name()].get('data_file', None)
        if data_file:
            return data_file
        
        return self.standard_data_file
    
    def get_experiments(self):
        """The configuration has been compiled before it is handed out
           to the client class, since some configurations can override
           others and none of that should concern other parts of the
           system.
        """
        return self._experiments
    
    def get_experiment(self, name):
        return self._experiments[name]
    
    def get_runs(self):
        runs = set()
        for exp in self._experiments.values():
            runs |= exp.get_runs()
        return runs
    
    
    def _valueOrListAllwaysAsList(self, value):
        if type(value) is list:
            return value
        elif value is None:
            return []
        else:
            return [value]
    
    def _compile_experiments(self):
        if not self.experiment_name():
            raise ValueError("No experiment chosen.")
        
        confDefs = {}
        
        if self.experiment_name() == "all":
            for exp_name in self._rawConfig['experiments']:
                confDefs[exp_name] = self._compile_experiment(exp_name)
        else:
            if self.experiment_name() not in self._rawConfig['experiments']:
                raise ValueError("Requested experiment '%s' not available." % self.experiment_name())
            confDefs[self.experiment_name()] = self._compile_experiment(self.experiment_name())
        
        return confDefs
    
    def _compile_experiment(self, exp_name):
        expDef = self._rawConfig['experiments'][exp_name]
        run_cfg = self.quick_runs if (self.options and self.options.quick) else self.runs
        
        return Experiment(exp_name, expDef, run_cfg,
                         self._rawConfig['virtual_machines'],
                         self._rawConfig['benchmark_suites'],
                         self._rawConfig['reporting'])
    
    
