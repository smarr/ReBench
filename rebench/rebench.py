#!/usr/bin/env python2.7
# ReBench is tool to run and document benchmarks.
#
# It is inspired by JavaStats implemented by Andy Georges.
# JavaStats can be found here: http://www.elis.ugent.be/en/JavaStats
#
# ReBench goes beyond the goals of JavaStats, no only by broaden the scope
# to not only Java VMs, but also by introducing facilities to evaluate
# other runtime characteristics of a VM beside pure execution time.
#
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

from .executor       import Executor
from .reporter       import FileReporter, Reporters, CliReporter,\
                            DiagramResultReporter, CodespeedReporter,\
                            CSVFileReporter
from .configurator   import Configurator
from .persistence import DataPointPersistence
from optparse import OptionParser, OptionGroup
import logging


class ReBench:
    
    def __init__(self):
        self.version = "0.3.0"
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
                           help="Do a quick benchmark run instead of a full, "
                                "statistical rigorous experiment.",
                           default=False)
        options.add_option("-d", "--debug", action="store_true", dest="debug",
                           default=False, help="Enable debug output.")
        options.add_option("-v", "--verbose", action="store_true",
                           dest="verbose", default=False,
                           help="Out more details in the report.")

        #options.add_option("-r", "--run", dest="run", default=None,
        #                   help="Specify a run definition to be used form "
        #                        " given config.")
        options.add_option("-n", "--without-nice", action="store_false",
                           dest="use_nice",
                           help="Used for debugging and environments without "
                                 " the tool nice.",
                           default=True)
        options.add_option("-o", "--out", dest="output_file", default=None,
                           help="Report is saved to the given file. "
                                "The report is always verbose.")
        options.add_option("-c", "--clean", action="store_true", dest="clean",
                           default=False,
                           help="Discard old data from the data file "
                                "(configured in the run description).")
        
        # now here some thing which have to be passed in to make codespeed
        # reporting complete
        codespeed = OptionGroup(options, "Reporting to Codespeed",
                                "Some of these parameters are mandatory for "
                                "reporting to codespeed")
        codespeed.add_option("--commit-id", dest="commit_id", default=None,
                             help="MANDATORY: when codespeed reporting is "
                                  " used, the commit-id has to be specified.")
        codespeed.add_option("--environment", dest="environment",
                             default=None,
                             help="MANDATORY: name the machine on which the "
                                  "results are obtained.")
        codespeed.add_option("--branch", dest="branch",
                             default="HEAD",
                             help="The branch for which the results have to be "
                                  "recorded, i.e., to which the commit belongs. Default: HEAD")
        codespeed.add_option("--executable", dest="executable",
                             default=None,
                             help="The executable name given to codespeed. Default: "
                                  "The name used for the virtual machine.")
        codespeed.add_option("--project", dest="project",
                             default=None,
                             help="The project name given to codespeed. Default: "
                                  "Value given in the config file.")
        codespeed.add_option("-f", "--disable-inc-report",
                             action="store_false", dest="report_incrementally",
                             default=True, help="Does a final report at the end instead of reporting incrementally.")
        codespeed.add_option("-s", "--disable-codespeed",
                             action="store_false", dest="use_codespeed",
                             default=True, help="Override configuration and "
                             "disable reporting to codespeed.")
        
        options.add_option_group(codespeed)
        return options
        

    
    def run(self, argv = None):
        if argv is None:
            argv = sys.argv
                    
        cli_options, args = self.shell_options().parse_args(argv[1:])
        if len(args) < 1:
            logging.error("<config> is a mandatory parameter and was not given. See --help for more information.")
            sys.exit(-1)
        

        self.config = Configurator(args[0], cli_options, *args[1:])
        
        self.execute_run()
        
    def execute_run(self):
        logging.debug("execute run: %s"%(self.config.experiment_name()))
        
        data = DataPointPersistence(self.config.data_file_name(), True)
        data.includeShebangLine(sys.argv)
        
        reporters = []
        if self.config.options.output_file:
            reporters.append(FileReporter(self.config.options.output_file, self.config))
            
        reporters.append(CliReporter(self.config))
        
        if self.config.visualization:
            reporters.append(DiagramResultReporter(self.config))
            
        if self.config.reporting:
            if ('codespeed' in self.config.reporting and
                self.config.options.use_codespeed):
                reporters.append(CodespeedReporter(self.config))
            if 'csv_file' in self.config.reporting:
                reporters.append(CSVFileReporter(self.config))
            if 'csv_raw' in self.config.reporting:
                data.setCsvRawFile(self.config.reporting['csv_raw'])
        
        # first load old data if available
        if self.config.options.clean:
            data.discardOldData()
        data.loadData()
        
        executor = Executor(self.config, data, Reporters(reporters))
        
        executor.execute()

# remember __import__(), obj.__dict__["foo"] == obj.foo


def main_func():
    return ReBench().run()

if __name__ == "__main__":
    sys.exit(main_func())
