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
from os.path import dirname, abspath
from pykwalify.core import Core
from pykwalify.errors import SchemaError
import yaml

from .configuration_error import ConfigurationError
from .model.experiment import Experiment
from .model.exp_run_details import ExpRunDetails
from .model.reporting import Reporting
from .model.executor import Executor
from .rebenchdb import ReBenchDB
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
        if self._name == "*":
            return True
        return bench.suite.name == self._name


class _BenchmarkFilter(_SuiteFilter):

    def __init__(self, suite_name, benchmark_name):
        super(_BenchmarkFilter, self).__init__(suite_name)
        self._benchmark_name = benchmark_name

    def matches(self, bench):
        if not super(_BenchmarkFilter, self).matches(bench):
            return False
        return bench.name == self._benchmark_name


class _MachineFilter(object):

    def __init__(self, machine):
        self._machine = machine

    def matches(self, machine):
        return machine == self._machine


class _RunFilter(object):

    def __init__(self, run_filters):
        self._executor_filters = []
        self._suite_filters = []
        self._machine_filters = []

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
            elif parts[0] == "m" and len(parts) == 2:
                self._machine_filters.append(_MachineFilter(parts[1]))
            else:
                raise RuntimeError("Unknown filter expression: " + run_filter)

    def applies_to_bench(self, bench):
        return (self._match(self._executor_filters, bench) and
                self._match(self._suite_filters, bench))

    def applies_to_machine(self, machine):
        return self._match(self._machine_filters, machine)

    @staticmethod
    def _match(filters, bench):
        if not filters:
            return True
        for run_filter in filters:
            if run_filter.matches(bench):
                return True
        return False


def load_config(file_name):
    """
    Load the file, verify that it conforms to the schema,
    and return the configuration.
    """
    try:
        with open(file_name, 'r') as conf_file:  # pylint: disable=unspecified-encoding
            data = yaml.safe_load(conf_file)
            validator = Core(
                source_data=data,
                schema_files=[dirname(__file__) + "/rebench-schema.yml"])
            try:
                validator.validate(raise_exception=True)
                validate_gauge_adapters(data)

                # add file name and directory to config to be able to use it when loading
                # for instance gauge adapters
                data['__file__'] = file_name
                data['__dir__'] = dirname(abspath(file_name))
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


def validate_gauge_adapters(raw_config):
    benchmark_suites = raw_config.get('benchmark_suites', {})
    for suite_name, suite in benchmark_suites.items():
        adapter = suite['gauge_adapter']
        if not isinstance(adapter, (dict, str)):
            raise UIError(("Gauge adapter for suite %s must be a string or a dictionary," +
                           "but is %s.\n") % (suite_name, type(adapter).__name__), None)

        if isinstance(adapter, dict) and len(adapter) != 1:
            raise UIError("When specifying a custom gauge adapter," +
                          " exactly one must to be specified." +
                          " Currently there are %d. (%s)\n" % (len(adapter), adapter), None)
    return True


class Configurator(object):

    def __init__(self, raw_config, data_store, ui, cli_options=None, cli_reporter=None,
                 exp_name=None, data_file=None, build_log=None, run_filter=None):
        self._raw_config_for_debugging = raw_config  # kept around for debugging only

        self.build_log = build_log or raw_config.get('build_log', 'build.log')
        self.data_file = data_file or raw_config.get('default_data_file', 'rebench.data')
        self._exp_name = exp_name or raw_config.get('default_experiment', 'all')
        self.artifact_review = raw_config.get('artifact_review', False)
        self.config_dir = raw_config.get('__dir__', None)
        self.config_file = raw_config.get('__file__', None)

        self._rebench_db_connector = None

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
            self.rebench_db = rdb_cfg
        else:
            self.rebench_db = {}
        if cli_options:
            if cli_options.db_server:
                self.rebench_db['db_url'] = cli_options.db_server
            self.rebench_db['send_to_rebench_db'] = cli_options.send_to_rebench_db

        self.options = cli_options
        self.ui = ui
        self.data_store = data_store
        self._process_cli_options()

        self.build_commands = {}

        self.run_filter = _RunFilter(run_filter)

        self._executors = raw_config.get('executors', {})
        self._suites_config = raw_config.get('benchmark_suites', {})

        experiments = raw_config.get('experiments', {})
        self._experiments = self._compile_experiments(experiments)

    @property
    def use_rebench_db(self):
        report_results = self.options is None or self.options.use_data_reporting
        return report_results and self.rebench_db and (
            self.rebench_db.get('send_to_rebench_db', False)
            or self.rebench_db.get('record_all', False))

    def get_rebench_db_connector(self):
        if not self.use_rebench_db:
            return None
        if self._rebench_db_connector:
            return self._rebench_db_connector

        if 'project_name' not in self.rebench_db:
            raise ConfigurationError(
                "No project_name defined in configuration file under reporting.rebenchdb.")

        if not self.options.experiment_name:
            raise ConfigurationError(
                "The experiment was not named, which is mandatory. "
                "This is needed to identify the data uniquely. "
                "It should also help to remember in which context it "
                "was recorded, perhaps relating to a specific CI job "
                "or confirming some hypothesis."
                "\n\n"
                "Use the --experiment option to set the name.")

        self._rebench_db_connector = ReBenchDB(
            self.rebench_db['db_url'], self.rebench_db['project_name'],
            self.options.experiment_name, self.ui)
        return self._rebench_db_connector

    def _process_cli_options(self):
        if self.options is None:
            return

        self.ui.init(self.options.verbose, self.options.debug)

    @property
    def do_builds(self):
        return self.options is not None and self.options.do_builds

    @property
    def discard_old_data(self):
        return self.options is not None and self.options.clean

    @property
    def experiment_name(self):
        return self._exp_name

    @property
    def reporting(self):
        return self._root_reporting

    @property
    def run_details(self):
        return self._root_run_details

    def has_executor(self, executor_name):
        return executor_name in self._executors

    def get_executor(self, executor_name, run_details, variables, action):
        if executor_name not in self._executors:
            raise ConfigurationError(
                "An experiment tries to use an undefined executor: %s" % executor_name)

        executor = Executor.compile(
            executor_name, self._executors[executor_name],
            run_details, variables, self.build_commands, action)
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
            runs |= exp.runs

        if self.options and self.options.setup_only:
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
