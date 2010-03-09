import sys
import yaml
import logging
import traceback

from contextpy import layer, globalActivateLayer
#proceed, activelayer, activelayers, after, around, before, base, globalDeactivateLayer

class Configurator:
    
    def __init__(self, fileName, cliOptions, runName = None):
        self._loadConfig(fileName)
        self._processCliOptions(cliOptions)
        self._runName = runName
    
    def __getattr__(self, name):
        return self._rawConfig[name]
    
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
            logging.debug("Enabled debug output.")
        else:
            logging.basicConfig(level=logging.ERROR)
            
        if options.quick:
            globalActivateLayer(layer("quick"))
            
        self.options = options
        
    def runName(self):
        return self._runName or self.standard_run
    
    def dataFileName(self):
        """@TODO: might add a commandline option 'ff' is just a placeholder here..."""
        return self.standard_dataFile
    
    def getBenchmarkConfigurations(self):
        """The configuration has be compiled before it can be handed out
           to the client class, since some configurations can override
           others
        """
        return self._compileBenchConfigurations(self.runName())
    
    def _valueOrListAllwaysAsList(self, value):
        if type(value) is list:
            return value
        elif value is None:
            return []
        else:
            return [value]
    
    def _compileBenchConfigurations(self, runName):
        runDef = self._rawConfig['run_definitions'][runName]
        #runDef.__missing__ = lambda itemName: None # does not work *grml*
        
        actions = self._valueOrListAllwaysAsList(runDef['actions'])
        _benchmarks = self._valueOrListAllwaysAsList(runDef['benchmark'])
        _input_size = self._valueOrListAllwaysAsList(runDef.get('input_size', None))
        
        _executions = self._valueOrListAllwaysAsList(runDef['executions']) 
        
        vmDefinitions = []
        
        # first step: adding the VM details to the run definition settings
        for vm in _executions:
            if type(vm) is dict:
                assert len(vm) == 1
                (vm, vmDetails) = vm.popitem()
            else:
                vmDetails = None
                
            vmDefinitions.append(self._compileVMDefinitionForVM(vm, vmDetails, _benchmarks, _input_size))
        
        # second step: specialize the suite definitions for the VMs
        suiteDefinitions = []
        for vmDef in vmDefinitions:
            suiteDefinitions += self._compileSuiteDefinitionsFromVMDef(vmDef)
        
        # third step: create final configurations to be executed
        configurationDefinitions = []
        for suite in suiteDefinitions:
            configurationDefinitions += self._compileConfigurations(suite)
        
        return (actions, configurationDefinitions)
    
    def _compileVMDefinitionForVM(self, vm, vmDetails, _benchmarks, _input_size):
        """Specializing the VM details in the run definitions with the settings from
           the VM definitions
        """
        if vmDetails:
            benchmarks = self._valueOrListAllwaysAsList(vmDetails['benchmark']) if 'benchmark' in vmDetails else _benchmarks
            input_size = self._valueOrListAllwaysAsList(vmDetails['input_size']) if 'input_size' in vmDetails else _input_size
        else:
            benchmarks = _benchmarks
            input_size = _input_size
            
        vmDef = self._rawConfig['virtual_machines'][vm].copy()
        vmDef['benchmark'] = benchmarks
        vmDef['input_size'] = input_size
        vmDef['name'] = vm 
        
        vmDef.setdefault('cores', [1])  # set a default value for the number cores list
        
        return vmDef

    def _compileSuiteDefinitionsFromVMDef(self, vmDef):
        """Specialize the benchmark suites for the given VM"""
        suiteDefs = []
        
        cleanVMDef = vmDef.copy()
        del cleanVMDef['benchmark']
        del cleanVMDef['input_size']
        
        for bench in vmDef['benchmark']:
            benchmark = self._rawConfig['benchmark_suites'][bench].copy()
            benchmark['name'] = bench
            
            if vmDef['input_size']:
                benchmark['input_size'] = vmDef['input_size']
                
            if 'location' not in benchmark:
                benchmark['location'] = vmDef['path']
             
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
    def __init__(self, name, performance_reader, suite, vm, extra_args = None):
        self.name = name
        self.extra_args = extra_args
        self.performance_reader = performance_reader
        self.suite = suite
        self.vm = vm
        
