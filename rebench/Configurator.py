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
from model.statistics       import Statistics

from contextpy import layer, globalActivateLayer
#proceed, activelayer, activelayers, after, around, before, base, globalDeactivateLayer

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
    # to warn users with old configurations
    outdated_suite_elements = {'ulimit' : 'max_runtime'}
    
    def __init__(self, fileName, cliOptions, runName = None):
        self._loadConfig(fileName)
        self._processCliOptions(cliOptions)
        self._runName = runName
        self.statistics = Statistics(**self._rawConfig.get('statistics', {}))
        
        self._config = self._compileBenchConfigurations(self.runName())
        
        self.visualization = self._rawConfig['run_definitions'][self.runName()].get('visualization', None)
        self.reporting     = self._rawConfig.get('reporting', {})
        self.reporting = dict_merge_recursively(self.reporting, self._rawConfig['run_definitions'][self.runName()].get('reporting', {}))
    
    def __getattr__(self, name):
        return self._rawConfig.get(name, None)
    
    def _loadConfig(self, file_name):
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
            
    def _processCliOptions(self, options):
        if options is None:
            return
        
        if options.debug:
            logging.basicConfig(level=logging.DEBUG)
            logging.getLogger().setLevel(logging.DEBUG)
            logging.debug("Enabled debug output.")
        else:
            logging.basicConfig(level=logging.ERROR)
            logging.getLogger().setLevel(logging.ERROR)
            
        if options.quick:
            globalActivateLayer(layer("quick"))
            
        self.options = options
        
    def runName(self):
        return self._runName or self.standard_run
    
    def dataFileName(self):
        """@TODO: might add a commandline option 'ff' is just a placeholder here..."""
        
        data_file = self._rawConfig['run_definitions'][self.runName()].get('data_file', None)
        if data_file:
            return data_file
        
        return self.standard_data_file
    
    def getBenchmarkConfigurations(self):
        """The configuration has be compiled before it can be handed out
           to the client class, since some configurations can override
           others
        """
        return self._config
    
    def _valueOrListAllwaysAsList(self, value):
        if type(value) is list:
            return value
        elif value is None:
            return []
        else:
            return [value]
    
    def _compileBenchConfigurations(self, runName):
        if runName not in self._rawConfig['run_definitions']:
            raise ValueError("Requested run_definition '%s' not available." % runName)
        
        runDef = self._rawConfig['run_definitions'][runName]
        
        # first thing, take the statistics configuration out of the runDef
        # and merge it with the global configuration
        self.statistics = self.statistics.combine(runDef.get('statistics', {}))
        
        
        actions = self._valueOrListAllwaysAsList(runDef['actions'])
        _benchmarks  = self._valueOrListAllwaysAsList(runDef.get(  'benchmark', None))
        _input_sizes = self._valueOrListAllwaysAsList(runDef.get('input_sizes', None))
        
        _executions = self._valueOrListAllwaysAsList(runDef['executions'])
        
        vmDefinitions = []
        
        # first step: adding the VM details to the run definition settings
        for vm in _executions:
            if type(vm) is dict:
                assert len(vm) == 1
                (vm, vmDetails) = vm.popitem()
            else:
                vmDetails = None
                
            vmDefinitions.append(self._compileVMDefinitionForVM(vm, vmDetails, _benchmarks, _input_sizes, runName))
        
        # second step: specialize the suite definitions for the VMs
        suiteDefinitions = []
        for vmDef in vmDefinitions:
            suiteDefinitions += self._compileSuiteDefinitionsFromVMDef(vmDef)
        
        # third step: create final configurations to be executed
        configurationDefinitions = []
        for suite in suiteDefinitions:
            configurationDefinitions += self._compileConfigurations(suite, actions)
        
        return configurationDefinitions
    
    def _compileVMDefinitionForVM(self, vm, vmDetails, _benchmarks, _input_sizes, runName):
        """Specializing the VM details in the run definitions with the settings from
           the VM definitions
        """
        if vmDetails:
            benchmarks = self._valueOrListAllwaysAsList(vmDetails['benchmark'])   if 'benchmark'   in vmDetails else _benchmarks
            input_sizes= self._valueOrListAllwaysAsList(vmDetails['input_sizes']) if 'input_sizes' in vmDetails else _input_sizes
            cores      = self._valueOrListAllwaysAsList(vmDetails['cores']) if 'cores' in vmDetails else None
        else:
            benchmarks = _benchmarks
            input_sizes= _input_sizes
            cores      = None
        
        if vm not in self._rawConfig['virtual_machines']:
            raise ValueError("The VM '%s' requested in %s was not found." % (vm, runName))
            
        vmDef = self._rawConfig['virtual_machines'][vm].copy()
        vmDef['benchmark'] = benchmarks
        vmDef['input_sizes'] = input_sizes
        vmDef['name'] = vm
        
        if cores is not None:
            vmDef['cores'] = cores
        else:
            vmDef.setdefault('cores', [1])  # set a default value for the number cores list
        
        return vmDef

    def _compileSuiteDefinitionsFromVMDef(self, vmDef):
        """Specialize the benchmark suites for the given VM"""
        suiteDefs = []
        
        cleanVMDef = vmDef.copy()
        del cleanVMDef['benchmark']
        del cleanVMDef['input_sizes']
        
        for bench in vmDef['benchmark']:
            benchmark = self._rawConfig['benchmark_suites'][bench].copy()
            benchmark['name'] = bench
            
            if vmDef['input_sizes']:
                benchmark['input_sizes'] = vmDef['input_sizes']
                
            if 'location' not in benchmark:
                benchmark['location'] = vmDef['path']
            if 'cores' not in benchmark:
                benchmark['cores'] = vmDef['cores']

            # REM: not sure whether that is the best place to encode that default
            if 'variable_values' not in benchmark:
                benchmark['variable_values'] = []
            
            # warn user when outdated config elements our found
            # they are not supported anymore
            for outdated, new in Configurator.outdated_suite_elements.iteritems():
                if outdated in benchmark:
                    logging.error("The config element '%s' was used. It is not supported anymore.", outdated)
                    logging.error("Please replace all uses of '%s' with '%s'.", outdated, new)
            
            benchmark['vm'] = cleanVMDef.copy() 
            suiteDefs.append(benchmark)
        
        return suiteDefs
    
    def _compileConfigurations(self, suite, actions):
        """Specialization of the configurations which get executed by using the
           suite definitions.
        """
        configs = []
        cleanSuite = suite.copy()
        
        del cleanSuite['benchmarks']
        del cleanSuite['performance_reader']
        del cleanSuite['vm']
        
        benchmarks = self._valueOrListAllwaysAsList(suite['benchmarks'])
        
        for bench in benchmarks:
            if type(bench) is dict:
                assert len(bench) == 1
                (name, bench) = bench.copy().popitem()
            else:
                name = bench
                bench = {}
            
            
            bench['name'] = name
            bench['suite'] = cleanSuite

            if 'performance_reader' not in bench:
                bench['performance_reader'] = suite['performance_reader']
            
            bench['vm'] = suite['vm']
            configs.append(BenchmarkConfig.create(bench, actions))
        
        return configs
