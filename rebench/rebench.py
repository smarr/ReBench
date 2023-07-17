#!/usr/bin/env python3
# ReBench is a tool to run and document benchmarks.
#
# It is inspired by JavaStats implemented by Andy Georges.
# JavaStats can be found here: http://www.elis.ugent.be/en/JavaStats
#
# ReBench goes beyond the goals of JavaStats, not only by broadening the scope
# to not only Java VMs, but also by introducing facilities to evaluate
# other runtime characteristics of an executor beside pure execution time.
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
import sys

from argparse import ArgumentParser, RawDescriptionHelpFormatter, SUPPRESS

from . import __version__ as rebench_version
from .executor import Executor, BatchScheduler, RoundRobinScheduler, \
    RandomScheduler, BenchmarkThreadExceptions
from .denoise import minimize_noise, restore_noise
from .environment import init_environment
from .persistence    import DataStore
from .rebenchdb      import get_current_time
from .reporter       import CliReporter
from .configurator   import Configurator, load_config
from .configuration_error import ConfigurationError
from .ui import UIError, UI


class ReBench(object):

    def __init__(self):
        self.version = rebench_version
        self.options = None
        self._config = None
        self.ui = UI()

    def shell_options(self):
        usage = """%(prog)s [options] <config> [exp_name] [e:$]* [s:$]* [m:$]*

Argument:
  config    required argument, file containing the experiment to be executed
  exp_name  optional argument, the name of an experiment definition
            from the config file
            If not provided, the configured default_experiment is used.
            If 'all' is given, all experiments will be executed.

  e:$       filter experiments to only include the named executor, example: e:EXEC1 e:EXEC3
  s:$       filter experiments to only include the named suite and possibly benchmark
            example: s:Suite1 s:*:Bench3

            Note, filters are combined with `or` semantics in the same group,
            i.e., executor or suite, and at least one filter needs to match per group.
            The suite name can also be given as * to match all possible suites.
  m:$       filter experiments to only include the named machines, example: m:machine1 m:machine2
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
                            help='Output more details during execution.')

        execution = parser.add_argument_group(
            'Execution Options', 'Adapt how ReBench executes benchmarks')
        execution.add_argument(
            '-in', '--invocations', action='store', dest='invocations',
            help='The number of times an executor is started to execute a run.',
            default=None, type=int)
        execution.add_argument(
            '-it', '--iterations', action='store', dest='iterations',
            help='The number of times a benchmark is to be executed within an executor invocation.',
            default=None, type=int)
        execution.add_argument(
            '-q', '--quick', action='store_true', dest='quick',
            help='Execute quickly. Identical with --iterations=1 --invocations=1',
            default=False)
        execution.add_argument(
            '--setup-only', action='store_true', dest='setup_only',
            help=('Build all executors and suites, and run one benchmark for each executor. ' +
                  'This ensures executors and suites are built. ' +
                  ' It Implies --iterations=1 --invocations=1.'),
            default=False)
        execution.add_argument(
            '-B', '--without-building', action='store_false', dest='do_builds',
            help='Disables execution of build commands for executors and suites.',
            default=True)
        execution.add_argument(
            '-s', '--scheduler', action='store', dest='scheduler',
            default='batch',
            help='execution order of benchmarks: '
                 'batch, round-robin, random [default: %(default)s]')
        execution.add_argument(
            '-E', '--no-execution', action='store_true', dest='no_execution',
            default=False,
            help='Disables execution.'
                 ' It allows to verify the configuration file and other parameters.')
        execution.add_argument(
            '-D', '--no-denoise', action='store_false', dest='use_denoise',
            default=True,
            help='Disable use of denoise, and thus, ' +
                 ' do not try to minimize interference from the system during benchmarking.')
        execution.add_argument(
            '-p', '--execution-plan', action='store_true', dest='execution_plan',
            default=False,
            help='Print execution plan.'
                 ' This outputs all executions that would be performed, without executing them.')

        data = parser.add_argument_group(
            'Data and Reporting',
            'Configure how recorded data is handled and reported')
        data.add_argument('-c', '--clean', action='store_true', dest='clean',
                          default=False,
                          help='Discard old data from the data file '
                               '(configured in the experiment).')
        data.add_argument('-r', '--rerun', action='store_true',
                          dest='do_rerun', default=False,
                          help='Rerun experiments, '
                               'and discard old data from data file.')
        data.add_argument('-f', '--faulty', action='store_true',
                          dest='include_faulty', default=False,
                          help='Include results of faulty or failing runs')
        data.add_argument('-df', '--data-file', dest='data_file', default=None,
                          help='Record all data into given file. '
                               'This overrides the configuration\'s settings.')
        data.add_argument('-b', '--build-log', dest='build_log', default=None,
                          help='File for the output of build commands.'
                               'This overrides the configuration\'s setting.')

        codespeed = parser.add_argument_group(
            'Reporting to Result Trackers',
            'Some of these parameters are mandatory for reporting to Codespeed')
        codespeed.add_argument('--commit-id', dest='commit_id', default=None,
                               help='MANDATORY: when Codespeed reporting is '
                                    ' used, the commit-id has to be specified.')
        codespeed.add_argument('--environment', dest='environment',
                               default=None,
                               help='MANDATORY: name the machine on which the '
                                    'results are obtained.')
        codespeed.add_argument('--executable', dest='executable',
                               default=None,
                               help='The executable name given to Codespeed. '
                                    'Default: The name used for the executor.')
        codespeed.add_argument('--project', dest='project',
                               default=None,
                               help='The project name given to Codespeed. '
                                    'Default: Value given in the config file.')
        codespeed.add_argument('-I', '--disable-inc-report',
                               action='store_false', dest='report_incrementally',
                               default=True, help='Creates a report at the '
                                                  'end instead of reporting '
                                                  'incrementally.')
        codespeed.add_argument('-R', '--disable-data-reporting',
                               action='store_false', dest='use_data_reporting',
                               default=True,
                               help='Override configuration and '
                                    'disable any reporting to Codespeed and ReBenchDB.')
        codespeed.add_argument('--git-repo', dest='git_repo', default=None,
                               help='Path to the git repository with the source for the ' +
                                    'experiment. This is useful when the experiment is run ' +
                                    'from a different location, for instance a RAM disk, or tmpfs.')

        rebench_db = parser.add_argument_group(
            'Reporting to ReBenchDB',
            'To interact with ReBenchDB, and provide environment information.')
        rebench_db.add_argument('--send', dest='send_to_rebench_db',
                                help='Send already recorded data to ReBenchDB',
                                action='store_true', default=False)
        rebench_db.add_argument('--db-server', dest='db_server',
                                default=None,
                                help='Set address of ReBenchDB server, overriding config file. '
                                     'Example: http://localhost:33333/rebenchdb/results')
        rebench_db.add_argument('-exp', '--experiment', dest='experiment_name',
                                default=None,
                                help='MANDATORY: name this experiment to uniquely identify the data'
                                     ' and be able to know what it was for'
                                     ' and possibly in which context it was recorded'
                                     ', perhaps relating to a specific CI job'
                                     ' or confirming some hypothesis.')
        rebench_db.add_argument('--branch', dest='branch',
                                default=None,
                                help='The branch for which the results have to '
                                     'be recorded, i.e., to which the commit'
                                     ' belongs. If not provided, ReBench will try to get'
                                     ' the name from git.')
        rebench_db.add_argument('--report-completion', dest='report_completion',
                                default=None, action='store_true',
                                help='Report the completion of the name experiment to ReBenchDB.')

        return parser

    @staticmethod
    def determine_exp_name_and_filters(filters):
        exp_name = filters[0] if filters and (
            not filters[0].startswith("e:") and
            not filters[0].startswith("s:") and
            not filters[0].startswith("m:")) else None
        exp_filter = [f for f in filters if (f.startswith("e:") or
                                             f.startswith("s:") or
                                             f.startswith("m:"))]
        return exp_name, exp_filter

    def _report_completion(self):
        rebench_db = self._config.get_rebench_db_connector()
        success, _ = rebench_db.send_completion(get_current_time())
        return success

    def run(self, argv=None):
        if argv is None:
            argv = sys.argv

        data_store = DataStore(self.ui)
        opt_parser = self.shell_options()
        args = opt_parser.parse_args(argv[1:])

        cli_reporter = CliReporter(args.verbose, self.ui)

        exp_name, exp_filter = self.determine_exp_name_and_filters(args.exp_filter)

        try:
            config = load_config(args.config[0])
            self._config = Configurator(config, data_store, self.ui, args,
                                        cli_reporter, exp_name, args.data_file,
                                        args.build_log, exp_filter)
        except ConfigurationError as exc:
            raise UIError(exc.message + "\n", exc)
        except ValueError as exc:
            raise UIError(exc.args[0] + "\n", exc)

        if args.report_completion:
            return self._report_completion()

        runs = self._config.get_runs()
        does_profiling = any(r.is_profiling() for r in runs)
        if not self._config.options.use_denoise:
            return self.load_data_and_execute_experiments(runs, data_store, False, False, None)
        else:
            denoise_result = None
            show_denoise_warnings = not (self._config.artifact_review
                                         or self._config.options.execution_plan)
            try:
                denoise_result = minimize_noise(show_denoise_warnings, self.ui, does_profiling)
                use_nice = denoise_result.use_nice
                use_shielding = denoise_result.use_shielding
                return self.load_data_and_execute_experiments(
                    runs, data_store, use_nice, use_shielding, denoise_result)
            finally:
                restore_noise(denoise_result, show_denoise_warnings, self.ui)

    def load_data_and_execute_experiments(self, runs, data_store,
                                          use_nice, use_shielding, denoise_result):
        init_environment(denoise_result, self.ui)
        data_store.load_data(runs, self._config.options.do_rerun)
        return self.execute_experiment(runs, use_nice, use_shielding)

    def execute_experiment(self, runs, use_nice, use_shielding):
        self.ui.verbose_output_info("Execute experiment: " + self._config.experiment_name + "\n")

        scheduler_class = {'batch':       BatchScheduler,
                           'round-robin': RoundRobinScheduler,
                           'random':      RandomScheduler}.get(self._config.options.scheduler)

        executor = Executor(runs, self._config.do_builds,
                            self.ui,
                            self._config.options.include_faulty,
                            self._config.options.debug,
                            scheduler_class,
                            self._config.build_log, self._config.artifact_review,
                            use_nice, use_shielding, self._config.options.execution_plan,
                            self._config.config_dir)

        if self._config.options.no_execution:
            return True
        else:
            if self._config.artifact_review:
                self.ui.output("Executing benchmarks for Artifact Review"
                                + " using the reported settings.")
            return executor.execute()


def main_func():
    try:
        rebench = ReBench()
        return 0 if rebench.run() else -1
    except KeyboardInterrupt:
        ui = UI()
        ui.debug_error_info("Aborted by user request\n")
        return -1
    except UIError as err:
        ui = UI()
        ui.error("\n" + err.message)
        return -1
    except BenchmarkThreadExceptions as exceptions:
        ui = UI()
        for ex in exceptions.exceptions:
            ui.error(str(ex) + "\n")
        return -1


if __name__ == "__main__":
    sys.exit(main_func())
