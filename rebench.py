#!/usr/bin/env python2.6
# ReBench is tool to run and document benchmarks.
#
# It is inspired by JavaStats implemented by Andy Georges.
# JavaStats can be found here: http://www.elis.ugent.be/en/JavaStats
#
# ReBench goes beyond the goals of JavaStats, no only by broaden the scope
# to not only Java VMs, but also by introducing facilities to evaluate
# other runtime characteristics of a VM beside pure execution time.
#
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

import sys

from Executor import Executor
from Reporter import *
from Configurator import Configurator
from DataAggregator import DataAggregator
from optparse import OptionParser

#from contextpy import layer, proceed, activelayer, activelayers, after, around, before, base, globalActivateLayer, globalDeactivateLayer

class ReBench:
    
    def __init__(self):
        self.version = "0.1.1"
        self.options = None
        self.config = None
    
    def shell_options(self):
        usage = """%prog [options] <config> [run_name]
        
Argument:
  config    required argument, file containing the run definition to be executed
  run_name  optional argument, the name of a run definition
            from the config file"""
        options = OptionParser(usage=usage, version="%prog " + self.version)
        
        options.add_option("-q", "--quick", action="store_true", dest="quick",
                           help="Do a quick benchmark run instead a full, statistical relevant experiment.", default=False)
        #TODO: Profiling is part of the run definition, not a cmd-line option...
        #options.add_option("-p", "--profile", action="store_true", dest="profile",
        #                   help="Profile dynamic characteristics instead measuring execution time.",
        #                   default=False)
        options.add_option("-d", "--debug", action="store_true", dest="debug", default=False,
                           help="Enable debug output.")
        options.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                           help="Out more details in the report.")

        #options.add_option("-r", "--run", dest="run", default=None,
        #                   help="Specify a run definition to be used form given config.")
        options.add_option("-n", "--without-nice", action="store_false", dest="use_nice",
                           help="Used for debugging and environments without the tool nice.",
                           default=True)
        options.add_option("-o", "--out", dest="output_file", default=None,
                           help="Report is saved to the given file. Report is always verbose.")
        options.add_option("-c", "--clean", action="store_true", dest="clean", default=False,
                           help="Discard old data from the data file (configured in the run description).")
        return options
        

    
    def run(self, argv = None):
        if argv is None:
            argv = sys.argv
            
        cli_options, args = self.shell_options().parse_args(argv[1:])
        if len(args) < 1:
            logging.error("<config> is a mandatory parameter and was not given. See --help for more information.")
            sys.exit(-1)
        

        self.config = Configurator(args[0], cli_options, args[1:])
        
        self.execute_run()
        
    def execute_run(self):
        logging.debug("execute run: %s"%(self.config.runName()))
        
        data     = DataAggregator(self.config.dataFileName(), self.config.options.clean, True)
        
        reporters = []
        if self.config.options.output_file:
            reporters.append(FileReporter(self.config.options.output_file))
            
        reporters.append(CliReporter())
        
        executor = Executor(self.config, data, Reporters(reporters))
        
        executor.execute()

# remember __import__(), obj.__dict__["foo"] == obj.foo
    
if __name__ == "__main__":
    sys.exit(ReBench().run())
