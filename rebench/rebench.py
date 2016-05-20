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
import logging
import sys

from optparse import OptionParser, OptionGroup

from .executor       import Executor, BatchScheduler, RoundRobinScheduler, \
                            RandomScheduler
from .persistence    import DataStore
from .configurator   import Configurator
from .configuration_error import ConfigurationError


class ReBench:
    
    def __init__(self):
        self.version = "0.7.4"
        self.options = None
        self._config = None
    
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
        options.add_option("-f", "--faulty", action="store_true",
                           dest="include_faulty", default=False,
                           help="Include results of faulty or failing runs")
        options.add_option("-v", "--verbose", action="store_true",
                           dest="verbose", default=False,
                           help="Out more details in the report.")

        options.add_option("-N", "--without-nice", action="store_false",
                           dest="use_nice",
                           help="Used for debugging and environments without "
                                 " the tool nice.",
                           default=True)
        options.add_option("-s", "--scheduler", action="store", type="string",
                           dest="scheduler", default="batch", help="execution "
                           "order of benchmarks: batch, round-robin, random "
                           "[default: %default]")
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
                                  "recorded, i.e., to which the commit belongs."
                                  " Default: HEAD")
        codespeed.add_option("--executable", dest="executable",
                             default=None,
                             help="The executable name given to codespeed. "
                                  "Default: The name used for the virtual "
                                  "machine.")
        codespeed.add_option("--project", dest="project",
                             default=None,
                             help="The project name given to codespeed. "
                                  "Default: Value given in the config file.")
        codespeed.add_option("-I", "--disable-inc-report",
                             action="store_false", dest="report_incrementally",
                             default=True, help="Does a final report at the "
                                                "end instead of reporting "
                                                "incrementally.")
        codespeed.add_option("-S", "--disable-codespeed",
                             action="store_false", dest="use_codespeed",
                             default=True, help="Override configuration and "
                             "disable reporting to codespeed.")
        
        options.add_option_group(codespeed)
        return options

    def run(self, argv = None):
        if argv is None:
            argv = sys.argv

        data_store = DataStore()
        cli_options, args = self.shell_options().parse_args(argv[1:])
        if len(args) < 1:
            logging.error("<config> is a mandatory parameter and was not given."
                          "See --help for more information.")
            sys.exit(-1)

        try:
            self._config = Configurator(args[0], data_store, cli_options, *args[1:])
        except ConfigurationError as e:
            logging.error(e.message)
            sys.exit(-1)
        data_store.load_data()
        self.execute_experiment()
        
    def execute_experiment(self):
        logging.debug("execute experiment: %s"%(self._config.experiment_name()))
        
        # first load old data if available
        if self._config.options.clean:
            pass

        scheduler_class = {'batch':       BatchScheduler,
                           'round-robin': RoundRobinScheduler,
                           'random':      RandomScheduler}.get(
                                                self._config.options.scheduler)
        executor = Executor(self._config.get_runs(), self._config.use_nice,
                            self._config.options.include_faulty,
                            scheduler_class)
        executor.execute()


def main_func():
    try:
        return ReBench().run()
    except KeyboardInterrupt:
        logging.info("Aborted by user request")

if __name__ == "__main__":
    sys.exit(main_func())
