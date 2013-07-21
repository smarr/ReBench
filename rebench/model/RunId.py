from numbers import Number
import logging
import os
import re
import sys


class RunId:
    _registry = {}
    
    @classmethod
    def reset(cls):
        cls._registry = {}
    
    @classmethod
    def create(cls, cfg, variables, terminationCriterion='total'):
        run = RunId(cfg, variables, terminationCriterion)
        if run in RunId._registry:
            return RunId._registry[run]
        else:
            RunId._registry[run] = run
            return run
    
    def __init__(self, cfg, variables, terminationCriterion='total'):
        self.cfg = cfg
        self.variables = self._stringify(variables)
        self.criterion = 'total'
    
    def __hash__(self):
        return (hash(self.cfg) ^ 
                hash(self.variables) ^ 
                hash(self.criterion))
        
    def _stringify(self, aTuple):
        result = ()
        for item in aTuple:
            if isinstance(item, Number) or item is None:
                result += (str(item), )
            else:
                result += (item, )
                
        return result
    
    def as_simple_string(self):
        return "%s %s %s" % (self.cfg.as_simple_string(), self.variables, self.criterion)
    
    def as_tuple(self):
        return self.cfg.as_tuple() + self.variables + (self.criterion, )
    
    def actions(self):
        return self.cfg.actions()
    
    def cmdline(self):
        cmdline  = ""
                
        vm_cmd = "%s/%s %s" % (os.path.abspath(self.cfg.vm['path']),
                               self.cfg.vm['binary'],
                               self.cfg.vm.get('args', ''))
            
        cmdline += vm_cmd 
        cmdline += self.cfg.suite['command']
        
        if self.cfg.extra_args is not None:
            cmdline += " %s" % (self.cfg.extra_args or "")
            
        (cores, input_size, var_val) = self.variables

        try:
            cmdline = cmdline % {'benchmark':self.cfg.name, 'input':input_size, 'variable':var_val, 'cores' : cores}
        except ValueError:
            self._report_cmdline_format_issue_and_exit(cmdline)
        except TypeError:
            self._report_cmdline_format_issue_and_exit(cmdline)
        
        return cmdline.strip()
    
    def __eq__(self, other):
        return (isinstance(other, self.__class__)
            and self.cmdline() == other.cmdline())

    def __ne__(self, other):
        return not self.__eq__(other)
    
    def _report_cmdline_format_issue_and_exit(self, cmdline):
        logging.critical("The configuration of %s contains improper Python format strings.", self.cfg.name)
         
        # figure out which format misses a conversion type
        without_conversion_type = re.findall("\%\(.*?\)(?![diouxXeEfFgGcrs\%])", cmdline)
        logging.error("The command line configured is: %s", cmdline)
        logging.error("The following elements do not have conversion types: \"%s\"",
                      '", "'.join(without_conversion_type))
        logging.error("This can be fixed by replacing for instance %s with %ss",
                      without_conversion_type[0],
                      without_conversion_type[0])
        sys.exit(-1)