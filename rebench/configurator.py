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
import subprocess
from os.path import dirname
import yaml
from pykwalify.core import Core
from pykwalify.errors import SchemaError

from .model.experiment import Experiment
from .model.exp_run_details import ExpRunDetails
from .model.reporting import Reporting
from .model.executor import Executor
from .ui import UIError, escape_braces

# Disable most logging for pykwalify
logging.getLogger('pykwalify').setLevel(logging.CRITICAL)
logging.getLogger('pykwalify').addHandler(logging.NullHandler())


class _ExecutorFilter(object):

    def __init__(self, name):
        self._name = name

    def matches(self, bench):
        return bench.suite.executor.name == self._name


class _SuiteFilter(object):

    def __init__(self, name):
        self._name = name

    def matches(self, bench):
        return bench.suite.name == self._name


class _BenchmarkFilter(_SuiteFilter):

    def __init__(self, suite_name, benchmark_name):
        super(_BenchmarkFilter, self).__init__(suite_name)
        self._benchmark_name = benchmark_name

    def matches(self, bench):
        if not super(_BenchmarkFilter, self).matches(bench):
            return False
        return bench.name == self._benchmark_name


class _RunFilter(object):

    def __init__(self, run_filters):
        self._executor_filters = []
        self._suite_filters = []

        if not run_filters:
            return

        for run_filter in run_filters:
            parts = run_filter.split(":")
            if parts[0] == "e":
                self._executor_filters.append(_ExecutorFilter(parts[1]))
            elif parts[0] == "s" and len(parts) == 2:
                self._suite_filters.append(_SuiteFilter(parts[1]))
            elif parts[0] == "s" and len(parts) == 3:
                self._suite_filters.append(_BenchmarkFilter(parts[1], parts[2]))
            else:
                raise Exception("Unknown filter expression: " + run_filter)

    def applies(self, bench):
        return (self._match(self._executor_filters, bench) and
                self._match(self._suite_filters, bench))

    @staticmethod
    def _match(filters, bench):
        if not filters:
            return True
        for run_filter in filters:
            if run_filter.matches(bench):
                return True
        return False


def can_set_niceness():
    """
    Check whether we can ask the operating system to influence the priority of
    our benchmarks.
    """
    output = subprocess.check_output(["nice", "-n-20", "echo", "test"],
                                     stderr=subprocess.STDOUT)
    if type(output) != str:  # pylint: disable=unidiomatic-typecheck
        output = output.decode('utf-8')
    if "cannot set niceness" in output or "Permission denied" in output:
        return False
    else:
        return True


def load_config(file_name):
    """
    Load the file, verify that it conforms to the schema,
    and return the configuration.
    """
    try:
        with open(file_name, 'r') as conf_file:
            data = yaml.safe_load(conf_file)
            validator = Core(
                source_data=data,
                schema_files=[dirname(__file__) + "/rebench-schema.yml"])
            try:
                validator.validate(raise_exception=True)
            except SchemaError as err:
                errors = [escape_braces(val_err) for val_err in validator.validation_errors]
                raise UIError(
                    "Validation of " + file_name + " failed.\n{ind}" +
                    "\n{ind}".join(errors) + "\n", err)
            return data
    except IOError as err:
        if err.errno == 2:
            assert err.strerror == "No such file or directory"
            raise UIError("The requested config file (%s) could not be opened. %s.\n"
                          % (file_name, err.strerror), err)
        raise UIError(str(err) + "\n", err)
    except yaml.YAMLError as err:
        raise UIError("Parsing of the config file "
                      + file_name + " failed.\nError " + str(err) + "\n", err)


class Configurator(object):

    def __init__(self, raw_config, data_store, ui, cli_options=None, cli_reporter=None,
                 exp_name=None, data_file=None, build_log=None, run_filter=None):
        self._raw_config_for_debugging = raw_config  # kept around for debugging only

        self._build_log = build_log or raw_config.get('build_log', 'build.log')
        self._data_file = data_file or raw_config.get('default_data_file', 'rebench.data')
        self._exp_name = exp_name or raw_config.get('default_experiment', 'all')

        # capture invocation and iteration settings and override when quick is selected
        invocations = cli_options.invocations if cli_options else None
        iterations = cli_options.iterations if cli_options else None
        if cli_options:
            if cli_options.setup_only or cli_options.quick:
                invocations = 1
                iterations = 1

        self._root_run_details = ExpRunDetails.compile(
            raw_config.get('runs', {}), ExpRunDetails.default(
                invocations, iterations))
        self._root_reporting = Reporting.compile(
            raw_config.get('reporting', {}), Reporting.empty(cli_reporter), cli_options, ui)

        # Construct ReBenchDB config
        rdb_cfg = raw_config.get('reporting', None)
        if rdb_cfg:
            rdb_cfg = rdb_cfg.get('rebenchdb', None)
        if rdb_cfg:
            self._rebench_db = rdb_cfg
        else:
            self._rebench_db = {}
        if cli_options:
            if cli_options.db_server:
                self._rebench_db['db_url'] = cli_options.db_server
            self._rebench_db['send_to_rebench_db'] = cli_options.send_to_rebench_db

        self._options = cli_options
        self._ui = ui
        self._data_store = data_store
        self._process_cli_options()

        self._build_commands = dict()

        self._run_filter = _RunFilter(run_filter)

        self._executors = raw_config.get('executors', {})
        self._suites_config = raw_config.get('benchmark_suites', {})

        experiments = raw_config.get('experiments', {})
        self._experiments = self._compile_experiments(experiments)

    @property
    def ui(self):
        return self._ui

    @property
    def build_log(self):
        return self._build_log

    @property
    def rebench_db(self):
        return self._rebench_db

    @property
    def use_rebench_db(self):
        return self._rebench_db and (self._rebench_db.get('send_to_rebench_db', False)
                                     or self._rebench_db.get('record_all', False))

    def _process_cli_options(self):
        if self._options is None:
            return

        self._ui.init(self._options.verbose, self._options.debug)

        if self._options.use_nice and not can_set_niceness():
            self._ui.error("Error: Process niceness can not be set.\n"
                           + "{ind}To execute benchmarks with highest priority,\n"
                           + "{ind}you might need root/admin rights.\n"
                           + "{ind}Deactivated usage of nice command.\n")
            self._options.use_nice = False

    @property
    def use_nice(self):
        return self._options is not None and self._options.use_nice

    @property
    def do_builds(self):
        return self._options is not None and self._options.do_builds

    @property
    def discard_old_data(self):
        return self._options is not None and self._options.clean

    @property
    def experiment_name(self):
        return self._exp_name

    @property
    def data_file(self):
        return self._data_file

    @property
    def reporting(self):
        return self._root_reporting

    @property
    def run_details(self):
        return self._root_run_details

    @property
    def options(self):
        return self._options

    @property
    def build_commands(self):
        return self._build_commands

    @property
    def run_filter(self):
        return self._run_filter

    @property
    def data_store(self):
        return self._data_store

    def has_executor(self, executor_name):
        return executor_name in self._executors

    def get_executor(self, executor_name, run_details, variables):
        executor = Executor.compile(
            executor_name, self._executors[executor_name],
            run_details, variables, self._build_commands)
        return executor

    def get_suite(self, suite_name):
        return self._suites_config[suite_name]

    def get_experiments(self):
        """The configuration has been compiled before it is handed out
           to the client class, since some configurations can override
           others and none of that should concern other parts of the
           system.
        """
        return self._experiments

    def get_experiment(self, name):
        return self._experiments[name]

    def get_runs(self):
        runs = set()
        for exp in list(self._experiments.values()):
            runs |= exp.get_runs()

        if self._options and self._options.setup_only:
            # filter out runs we don't need to trigger a build
            runs_with_builds = set()
            build_commands = set()

            for run in runs:
                commands = run.build_commands()
                if not build_commands >= commands:
                    runs_with_builds.add(run)
                    build_commands.update(commands)
            runs = runs_with_builds
        return runs

    def _compile_experiments(self, experiments):
        results = {}

        if self._exp_name == 'all':
            for exp_name in experiments:
                results[exp_name] = self._compile_experiment(exp_name, experiments[exp_name])
        else:
            if self._exp_name not in experiments:
                raise ValueError("Requested experiment '%s' not available." %
                                 self._exp_name)
            results[self._exp_name] = self._compile_experiment(
                self._exp_name, experiments[self._exp_name])

        return results

    def _compile_experiment(self, exp_name, experiment):
        return Experiment.compile(exp_name, experiment, self)
