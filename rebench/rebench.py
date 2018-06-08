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
from argparse import ArgumentParser, RawDescriptionHelpFormatter, SUPPRESS

from .executor       import Executor, BatchScheduler, RoundRobinScheduler, \
                            RandomScheduler
from .persistence    import DataStore
from .reporter       import CliReporter
from .configurator   import Configurator
from .configuration_error import ConfigurationError


class ReBench:
    
    def __init__(self):
        self.version = "0.10.1"
        self.options = None
        self._config = None
    
    def shell_options(self):
        usage = """%(prog)s [options] <config> [exp_name] [vm:$]* [s:$]*
        
Argument:
  config    required argument, file containing the experiment to be executed
  exp_name  optional argument, the name of a experiment definition
            from the config file
  vm:$      filter experiments to only include the named VM, example: vm:VM1 vm:VM3
  s:$       filter experiments to only include the named suite and possibly benchmark
            example: s:Suite1 s:Suite2:Bench3

            Note, filters are combined with `or` semantics in the same group,
            i.e., vm or suite, and at least one filter needs to match per group.
"""

        parser = ArgumentParser(
            usage=usage, add_help=False,
            formatter_class=RawDescriptionHelpFormatter)

        parser.add_argument('config', nargs=1, help=SUPPRESS)
        parser.add_argument('exp_filter', nargs='*', help=SUPPRESS)

        basics = parser.add_argument_group('Basic Options')
        basics.add_argument('-h', '--help', action='help',
                            help='Show this help message and exit')
        basics.add_argument('--version', action='version',
                            version="%(prog)s " + self.version)
        basics.add_argument('-d', '--debug', action='store_true', dest='debug',
                            default=False, help='Enable debug output')
        basics.add_argument('-v', '--verbose', action='store_true',
                            dest='verbose', default=False,
                            help='Output more details in the report.')

        execution = parser.add_argument_group(
            'Execution Options', 'Adapt how ReBench executes benchmarks')
        execution.add_argument(
            '-q', '--quick', action='store_true', dest='quick',
            help='Do a quick benchmark run instead of a full, '
                 'statistical rigorous experiment.',
            default=False)
        execution.add_argument(
            '-N', '--without-nice', action='store_false', dest='use_nice',
            help='Used for debugging and environments without the tool nice.',
            default=True)
        execution.add_argument(
            '-s', '--scheduler', action='store', dest='scheduler',
            default='batch',
            help='execution order of benchmarks: '
                 'batch, round-robin, random [default: %(default)s]')

        data = parser.add_argument_group(
            'Data and Reporting',
            'Configure how recorded data is handled and reported')
        data.add_argument('-c', '--clean', action='store_true', dest='clean',
                          default=False,
                          help='Discard old data from the data file '
                               '(configured in the experiment).')
        data.add_argument('-r', '--rerun', action='store_true',
                          dest='do_rerun', default=False,
                          help='Rerun experiments, ' +
                               'and discard old data from data file.')
        data.add_argument('-f', '--faulty', action='store_true',
                          dest='include_faulty', default=False,
                          help='Include results of faulty or failing runs')
        data.add_argument('-o', '--out', dest='output_file', default=None,
                          help='Report is saved to the given file. '
                               'The report is always verbose.')

        codespeed = parser.add_argument_group(
            'Reporting to Codespeed',
            'Some of these parameters are mandatory for reporting to Codespeed')
        codespeed.add_argument('--commit-id', dest='commit_id', default=None,
                               help='MANDATORY: when codespeed reporting is '
                                    ' used, the commit-id has to be specified.')
        codespeed.add_argument('--environment', dest='environment',
                               default=None,
                               help='MANDATORY: name the machine on which the '
                                    'results are obtained.')
        codespeed.add_argument('--branch', dest='branch',
                               default='HEAD',
                               help='The branch for which the results have to '
                                    'be recorded, i.e., to which the commit'
                                    ' belongs. Default: HEAD')
        codespeed.add_argument('--executable', dest='executable',
                               default=None,
                               help='The executable name given to codespeed. '
                                    'Default: The name used for the virtual '
                                    'machine.')
        codespeed.add_argument('--project', dest='project',
                               default=None,
                               help='The project name given to codespeed. '
                                    'Default: Value given in the config file.')
        codespeed.add_argument('-I', '--disable-inc-report',
                               action='store_false', dest='report_incrementally',
                               default=True, help='Does a final report at the '
                                                  'end instead of reporting '
                                                  'incrementally.')
        codespeed.add_argument('-S', '--disable-codespeed',
                               action='store_false', dest='use_codespeed',
                               default=True,
                               help='Override configuration and '
                                    'disable reporting to codespeed.')
        
        return parser

    def run(self, argv = None):
        if argv is None:
            argv = sys.argv

        data_store = DataStore()
        opt_parser = self.shell_options()
        args = opt_parser.parse_args(argv[1:])

        cli_reporter = CliReporter(args.verbose)

        # interpret remaining args
        exp_filter = args.exp_filter
        exp_name = exp_filter[0] if len(exp_filter) > 0 and (
            not exp_filter[0].startswith("vm:") and
            not exp_filter[0].startswith("s:")) else "all"
        exp_filter = [f for f in exp_filter if (f.startswith("vm:") or
                                                f.startswith("s:"))]

        try:
            config_filename = args.config[0]
            self._config = Configurator(config_filename, data_store, args,
                                        cli_reporter, exp_name, None,
                                        exp_filter)
        except ConfigurationError as e:
            logging.error(e.message)
            sys.exit(-1)
        data_store.load_data()
        return self.execute_experiment()
        
    def execute_experiment(self):
        logging.debug("execute experiment: %s" % self._config.experiment_name())
        
        # first load old data if available
        if self._config.options.clean:
            pass

        scheduler_class = {'batch':       BatchScheduler,
                           'round-robin': RoundRobinScheduler,
                           'random':      RandomScheduler}.get(self._config.options.scheduler)
        runs = self._config.get_runs()
        if self._config.options.do_rerun:
            DataStore.discard_data_of_runs(runs)

        executor = Executor(runs, self._config.use_nice,
                            self._config.options.include_faulty,
                            self._config.options.verbose,
                            scheduler_class,
                            self._config.build_log)
        return executor.execute()


def main_func():
    try:
        return 0 if ReBench().run() else -1
    except KeyboardInterrupt:
        logging.info("Aborted by user request")
        return -1


if __name__ == "__main__":
    sys.exit(main_func())
