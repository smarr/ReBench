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
import logging
import traceback
import yaml

from Executor import Executor
from Reporter import Reporter
from optparse import OptionParser

class ReBench:
    
    def __init__(self):
        self.version = "0.0.9"
        self.options = None
        self.config = None
    
    def shell_options(self):
        usage = """%prog [options] [rundefinition]
        
Argument:
  rundefinition  optional argument specifying a run definition
                 from the config file"""
        options = OptionParser(usage=usage, version="%prog " + self.version)
        
        options.add_option("-p", "--profile", action="store_true", dest="profile",
                           help="Profile dynamic characteristics instead measuring execution time.",
                           default=False)
        options.add_option("-d", "--debug", action="store_true", dest="debug", default=False,
                           help="Enable debug output.")
        options.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                           help="Out more details in the report.")
        options.add_option("-c", "--config", dest="config", default="%s.conf"%(self.__class__.__name__.lower()),
                           help="Config file to be used.")
        options.add_option("-r", "--run", dest="run", default=None,
                           help="Specify a run definition to be used form given config.")
        options.add_option("-n", "--without-nice", action="store_false", dest="use_nice",
                           help="Used for debugging and environments without the tool nice.",
                           default=False)
        options.add_option("-o", "--out", dest="output_file", default=None,
                           help="Report is saved to the given file. Report is always verbose.")
        return options
        
    def load_config(self, file_name):
        try:
            f = file(file_name, 'r')
            return yaml.load(f)
        except IOError:
            logging.error("There was an error opening the config file (%s)."%(file_name))
            logging.error(traceback.format_exc(0))
            sys.exit(-1)
        except yaml.YAMLError:
            logging.error("Failed parsing the config file (%s)."%(file_name))
            logging.error(traceback.format_exc(0))
            sys.exit(-1) 
    
    def run(self, argv = None):
        if argv is None:
            argv = sys.argv
            
        self.options, args = self.shell_options().parse_args(argv[1:])
        
        if self.options.debug:
            logging.basicConfig(level=logging.DEBUG)
            logging.debug("Enabled debug output.")
        else:
            logging.basicConfig(level=logging.ERROR)
            
        self.config = self.load_config(self.options.config)
        # add some basic options to config
        self.config["options"] = {}
        self.config["options"]["use_nice"] = self.options.use_nice
                
        run = self.extract_rundefinition_from_options()
        if run is None:
            run = self.config["standard_run"]
            
        self.execute_run(run)
        
    def execute_run(self, run):
        logging.debug("execute run: %s"%(run))
        
        if type(run) == str:
            run = self.config["run_definitions"][run]
        
        executor = Executor(self.config, **run)
        executor.execute()
        results = executor.get_results()
        
        reporter = Reporter(self.config, self.options.output_file)
        reporter.set_data(results)
        reporter.report(self.options.verbose)
            
    def extract_rundefinition_from_options(self):
        if self.options.run != None:
            return self.options.run
        else:
            # TODO: implement complex CLI interface to provide adhoc run definitions 
            pass


# remember __import__(), obj.__dict__["foo"] == obj.foo
    
if __name__ == "__main__":
    sys.exit(ReBench().run())
