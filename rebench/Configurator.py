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
    
    def __init__(self, fileName, cliOptions, runName = None):
        self._loadConfig(fileName)
        self._processCliOptions(cliOptions)
        self._runName = runName
        self.statistics = self._rawConfig.get('statistics', {})
        
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
        runDef = self._rawConfig['run_definitions'][runName]
        
        # first thing, take the statistics configuration out of the runDef
        # and merge it with the global configuration
        self.statistics = dict(self.statistics, **runDef.get('statistics', {}))
        
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
                
            vmDefinitions.append(self._compileVMDefinitionForVM(vm, vmDetails, _benchmarks, _input_sizes))
        
        # second step: specialize the suite definitions for the VMs
        suiteDefinitions = []
        for vmDef in vmDefinitions:
            suiteDefinitions += self._compileSuiteDefinitionsFromVMDef(vmDef)
        
        # third step: create final configurations to be executed
        configurationDefinitions = []
        for suite in suiteDefinitions:
            configurationDefinitions += self._compileConfigurations(suite)
        
        return (actions, configurationDefinitions)
    
    def _compileVMDefinitionForVM(self, vm, vmDetails, _benchmarks, _input_sizes):
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
             
            benchmark['vm'] = cleanVMDef.copy() 
            suiteDefs.append(benchmark)
        
        return suiteDefs
    
    def _compileConfigurations(self, suite):
        """Specialization of the configurations which get executed by using the
           suite definitions.
        """
        configs = []
        cleanSuite = suite.copy()
        
        del cleanSuite['benchmarks']
        del cleanSuite['performance_reader']
        del cleanSuite['vm']
        
        for bench in suite['benchmarks']:
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
            configs.append(BenchmarkConfig(**bench))
        
        return configs

class BenchmarkConfig:
    _registry = {}
    
    @classmethod
    def reset(cls):
        cls._registry = {}
    
    @classmethod
    def getConfig(cls, name, suiteName, vmName, extra_args = None):
        tmp = BenchmarkConfig(name, None, {'name':suiteName}, {'name':vmName}, extra_args, False)
        if tmp not in cls._registry:
            raise ValueError("Requested configuration is not available: " + (cls, name, suiteName, vmName, extra_args).__str__())
        
        return cls._registry[tmp]
    
    def __init__(self, name, performance_reader, suite, vm, extra_args = None, do_register = True):
        self.name = name
        self.extra_args = str(extra_args) if extra_args else None
        self.performance_reader = performance_reader
        self.suite = suite
        self.vm = vm
        
        if do_register:
            if self in BenchmarkConfig._registry:
                raise ValueError("Configuration is already registered.")
            else:
                BenchmarkConfig._registry[self] = self
        
    def __str__(self):
        return "%s, vm:%s, suite:%s, args:'%s'" % (self.name, self.vm['name'], self.suite['name'], self.extra_args or '')
        
    def __eq__(self, other):
        """I am not exactly sure whether that will be right, or whether
           I actually need to take the whole suite and vm dictionaries
           into account"""
        if type(other) != type(self):
            return False
        
        return (    self.name == other.name
                and self.extra_args == other.extra_args
                and self.suite['name'] == other.suite['name']
                and self.vm['name'] == other.vm['name'])
                
    def __ne__(self, other):
        return not self.__eq__(other)
    
    def __hash__(self):
        return (hash(self.name) ^ 
                hash(self.extra_args) ^ 
                hash(self.suite['name']) ^
                hash(self.vm['name']))
    
    def as_tuple(self):
        return (self.name, self.vm['name'], self.suite['name'], self.extra_args)
        
    @classmethod
    def tuple_mapping(cls):
        return {'bench' : 0, 'vm' : 1, 'suite' : 2, 'extra_args' : 3}
