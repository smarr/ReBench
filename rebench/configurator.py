# Copyright (c) 2009-2014 Stefan Marr <http://www.stefan-marr.de/>
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
import logging
import subprocess
import traceback
from .model.runs_config import RunsConfig, QuickRunsConfig
from .model.experiment  import Experiment


class Configurator:

    def __init__(self, file_name, data_store, cli_options = None,
                 exp_name = None, standard_data_file = None):
        self._raw_config = self._load_config(file_name)
        if standard_data_file:
            self._raw_config['standard_data_file'] = standard_data_file

        self._options    = self._process_cli_options(cli_options)
        self._exp_name   = exp_name
        
        self.runs        = RunsConfig(     **self._raw_config.get(      'runs', {}))
        self.quick_runs  = QuickRunsConfig(**self._raw_config.get('quick_runs', {}))

        self._data_store = data_store
        self._experiments = self._compile_experiments()

        # TODO: does visualization work?
        # self.visualization = self._raw_config['experiments'][self.experiment_name()].get('visualization', None)
            
    @staticmethod
    def _load_config(file_name):
        import yaml
        try:
            f = file(file_name, 'r')
            return yaml.load(f)
        except IOError:
            logging.error("An error occurred on opening the config file (%s)."
                          % file_name)
            logging.error(traceback.format_exc(0))
            sys.exit(-1)
        except yaml.YAMLError:
            logging.error("Failed parsing the config file (%s)." % file_name)
            logging.error(traceback.format_exc(0))
            sys.exit(-1)

    def _process_cli_options(self, options):
        if options is None:
            return
        
        if options.debug:
            if options.verbose:
                logging.basicConfig(level=logging.NOTSET)
                logging.getLogger().setLevel(logging.NOTSET)
                logging.debug("Enabled verbose debug output.")
            else:
                logging.basicConfig(level=logging.DEBUG)
                logging.getLogger().setLevel(logging.DEBUG)
                logging.debug("Enabled debug output.")
        else:
            logging.basicConfig(level=logging.ERROR)
            logging.getLogger().setLevel(logging.ERROR)

        if options.use_nice:
            if not self._can_set_niceness():
                logging.error("Process niceness cannot be set currently. "
                              "To execute benchmarks with highest priority, "
                              "you might need root/admin rights.")
                logging.error("Deactivated usage of nice command.")
                options.use_nice = False
                    
        return options

    @staticmethod
    def _can_set_niceness():
        output = subprocess.check_output(["nice", "-n-20", "echo", "test"],
                                         stderr=subprocess.STDOUT)
        if "cannot set niceness" in output or "Permission denied" in output:
            return False
        else:
            return True

    @property
    def options(self):
        return self._options

    @property
    def use_nice(self):
        return self.options is not None and self.options.use_nice
        
    def experiment_name(self):
        return self._exp_name or self._raw_config['standard_experiment']
    
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
    
    def _compile_experiments(self):
        if not self.experiment_name():
            raise ValueError("No experiment chosen.")
        
        conf_defs = {}
        
        if self.experiment_name() == "all":
            for exp_name in self._raw_config['experiments']:
                conf_defs[exp_name] = self._compile_experiment(exp_name)
        else:
            if self.experiment_name() not in self._raw_config['experiments']:
                raise ValueError("Requested experiment '%s' not available." %
                                 self.experiment_name())
            conf_defs[self.experiment_name()] = self._compile_experiment(
                                                        self.experiment_name())
        
        return conf_defs

    def _compile_experiment(self, exp_name):
        exp_def = self._raw_config['experiments'][exp_name]
        run_cfg = (self.quick_runs if (self.options and self.options.quick)
                                   else self.runs)
        
        return Experiment(exp_name, exp_def, run_cfg,
                          self._raw_config['virtual_machines'],
                          self._raw_config['benchmark_suites'],
                          self._raw_config.get('reporting', {}),
                          self._data_store,
                          self._raw_config.get('standard_data_file', None),
                          self._options.clean if self._options else False,
                          self._options)
