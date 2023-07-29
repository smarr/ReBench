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
import subprocess
import json
import sys
from datetime import datetime
from unittest import skipIf
from .mock_http_server import MockHTTPServer
from .rebench_test_case import ReBenchTestCase
from .persistence import TestPersistence

from ..persistence import DataStore, _ReBenchDB
from ..rebenchdb import ReBenchDB

from ..configurator import Configurator, load_config
from ..environment import git_not_available, git_repo_not_initialized
from ..executor import Executor
from ..model.benchmark import Benchmark
from ..model.benchmark_suite import BenchmarkSuite
from ..model.executor import Executor as ExecutorConf
from ..model.exp_run_details import ExpRunDetails
from ..model.measurement import Measurement
from ..model.run_id import RunId
from ..rebench import ReBench


class PersistencyTest(ReBenchTestCase):
    def test_de_serialization(self):
        data_store = DataStore(self.ui)
        executor = ExecutorConf("MyVM", '', '',
                                None, None, None, None, None, None, "benchmark", {})
        suite = BenchmarkSuite("MySuite", executor, '', '', None, None,
                               None, None, None, None)
        benchmark = Benchmark("Test Bench [>", "Test Bench [>", None,
                              suite, None, None, ExpRunDetails.default(None, None),
                              None, data_store)

        run_id = RunId(benchmark, 1000, 44, 'sdf sdf sdf sdfsf', 'machine-22')
        measurement = Measurement(43, 45, 2222.2222, 'ms', run_id, 'foobar crit')

        serialized = measurement.as_str_list()
        deserialized = Measurement.from_str_list(data_store, serialized)

        self.assertEqual(deserialized.criterion, measurement.criterion)
        self.assertEqual(deserialized.value, measurement.value)
        self.assertEqual(deserialized.unit, measurement.unit)
        self.assertEqual(deserialized.invocation, measurement.invocation)
        self.assertEqual(deserialized.iteration, measurement.iteration)

        self.assertEqual(deserialized.run_id, measurement.run_id)

    def test_iteration_invocation_semantics(self):
        # Executes first time
        ds = DataStore(self.ui)
        cnf = Configurator(load_config(self._path + '/persistency.conf'),
                           ds, self.ui, data_file=self._tmp_file)
        ds.load_data(None, False)
        self._assert_runs(cnf, 1, 0, 0)

        ex = Executor(cnf.get_runs(), False, self.ui)
        ex.execute()

        self._assert_runs(cnf, 1, 10, 10)

        # Execute a second time, should not add any data points,
        # because goal is already reached
        ds2 = DataStore(self.ui)
        cnf2 = Configurator(load_config(self._path + '/persistency.conf'),
                            ds2, self.ui, data_file=self._tmp_file)
        ds2.load_data(None, False)

        self._assert_runs(cnf2, 1, 10, 10)

        ex2 = Executor(cnf2.get_runs(), False, self.ui)
        ex2.execute()

        self._assert_runs(cnf2, 1, 10, 10)

    def test_data_discarding(self):
        # Executes first time
        ds = DataStore(self.ui)
        cnf = Configurator(load_config(self._path + '/persistency.conf'),
                           ds, self.ui, data_file=self._tmp_file)
        ds.load_data(None, False)

        self._assert_runs(cnf, 1, 0, 0)

        ex = Executor(cnf.get_runs(), False, self.ui)
        ex.execute()

        self._assert_runs(cnf, 1, 10, 10)

        # Execute a second time, this time, discard the data first, and then rerun
        ds2 = DataStore(self.ui)
        cnf2 = Configurator(load_config(self._path + '/persistency.conf'),
                            ds2, self.ui, data_file=self._tmp_file)
        run2 = cnf2.get_runs()
        ds2.load_data(run2, True)

        self._assert_runs(cnf2, 1, 0, 0)

        ex2 = Executor(run2, False, self.ui)
        ex2.execute()

        self._assert_runs(cnf2, 1, 10, 10)

    @skipIf(git_not_available() or git_repo_not_initialized(),
        "git source info not available, but needed for reporting to ReBenchDB")
    def test_rebench_db(self):
        option_parser = ReBench().shell_options()
        cmd_config = option_parser.parse_args(['--experiment=Test', 'persistency.conf'])

        server = MockHTTPServer()

        try:
            self._exec_rebench_db(cmd_config, server)
            server.process_and_shutdown()

            self.assertEqual(1, server.get_number_of_put_requests())
        finally:
            server.process_and_shutdown()

    def test_disabled_rebench_db(self):
        option_parser = ReBench().shell_options()
        cmd_config = option_parser.parse_args(['--experiment=Test', '-R', 'persistency.conf'])

        server = MockHTTPServer()

        try:
            self._exec_rebench_db(cmd_config, server)
            server.process_and_shutdown()

            self.assertEqual(0, server.get_number_of_put_requests())
        finally:
            server.process_and_shutdown()

    def _exec_rebench_db(self, cmd_config, server):
        port = server.get_free_port()

        server.start()
        ds = DataStore(self.ui)

        raw_config = load_config(self._path + '/persistency.conf')
        del raw_config['reporting']['codespeed']
        raw_config['reporting']['rebenchdb'] = {
            'db_url': 'http://localhost:' + str(port),
            'repo_url': 'http://repo.git',
            'project_name': 'Persistency Test',
            'send_to_rebench_db': True,
            'record_all': True}

        cnf = Configurator(raw_config, ds, self.ui, cmd_config, data_file=self._tmp_file)
        ds.load_data(None, False)

        self._assert_runs(cnf, 1, 0, 0)

        ex = Executor(cnf.get_runs(), False, self.ui)
        ex.execute()

        run = list(cnf.get_runs())[0]
        run.close_files()

    def test_check_file_lines(self):
        self._load_config_and_run()

        with open(self._tmp_file, 'r') as file: # pylint: disable=unspecified-encoding
            lines = file.readlines()

        command = self.get_line_after_char('#!', lines[0])
        self.assertEqual(command, subprocess.list2cmdline(sys.argv))

        time = self.get_line_after_char('Start:', lines[1])
        self.assertTrue(self.is_valid_time(time))

        self.assertIsNotNone(json.loads(self.get_line_after_char('Environment:', lines[2])))
        self.assertIsNotNone(json.loads(self.get_line_after_char('Source:', lines[3])))

        column_headers = lines[4].split("\t")
        # remove the newline character from the last column header
        column_headers[-1] = column_headers[-1].rstrip('\n')

        expected_headers = Measurement.get_column_headers()
        self.assertEqual(column_headers, expected_headers)

        self.assertEqual(len((lines[5]).split("\t")), len(column_headers),
                         'expected same number of column headers as data columns')

    def get_line_after_char(self, char, line):
        if char in line:
            get_line = line.split(char)
            return (get_line[1]).strip()
        return None

    def is_valid_time(self, time_str):
        try:
            datetime.strptime(time_str, '%Y-%m-%dT%H:%M:%S.%f%z')
            return True
        except ValueError:
            return False

    def _load_config_and_run(self, args=None):
        ds = DataStore(self.ui)
        cnf = Configurator(load_config(self._path + '/persistency.conf'),
                           ds, self.ui, args, data_file=self._tmp_file)
        ds.load_data(None, False)
        ex = Executor(cnf.get_runs(), False, self.ui)
        ex.execute()

    def test_check_single_csv_header(self):
        """Check that there is only one csv header in the file"""
        # first run
        self._load_config_and_run()

        # second run, requesting more invocations
        opt_parser = ReBench().shell_options()
        args = opt_parser.parse_args(['-in', '20', '-R', self._path + '/persistency.conf'])
        self._load_config_and_run(args)

        with open(self._tmp_file, 'r') as file: # pylint: disable=unspecified-encoding
            lines = file.readlines()

        # count the number of lines starting with 'invocation'
        invocation_lines = [line for line in lines if line.startswith('invocation')]
        self.assertEqual(len(invocation_lines), 1)

    def _create_dummy_rebench_db_persistence(self):
        class _Cfg(object):
            @staticmethod
            def get_rebench_db_connector():
                return None

        return _ReBenchDB(_Cfg(), None, self.ui)

    def _run_exp_to_get_data_points_with_inconsistent_set_of_criteria(self):
        yaml = load_config(self._path + '/features/issue_16.conf')
        yaml['executors']['TestRunner']['executable'] = 'features/issue_16_vm2.py'
        cnf = Configurator(yaml, DataStore(self.ui),
                           self.ui, exp_name='Test1',
                           data_file=self._tmp_file)
        runs = cnf.get_runs()
        persistence = TestPersistence()
        persistence.use_on(runs)
        run_id_obj = list(runs)[0]
        ex = Executor(runs, False, self.ui)
        ex.execute()
        return {list(runs)[0]: persistence.get_data_points()}, run_id_obj

    def _assert_criteria_index_structure(self, criteria_index):
        criteria = ['bar', 'baz', 'total', 'foo']
        for i, c in enumerate(criteria_index):
            self.assertEqual(i, c['i'])
            self.assertEqual(criteria[i], c['c'])
            self.assertEqual('ms', c['u'])

    def _assert_run_id_structure(self, run_id, run_id_obj):
        self.assertEqual(run_id['varValue'], run_id_obj.var_value)
        self.assertIsNone(run_id['varValue'])

        self.assertEqual(run_id['machine'], run_id_obj.machine)
        self.assertIsNone(run_id['machine'])

        self.assertEqual(run_id['location'], run_id_obj.location)
        self.assertEqual(run_id['inputSize'], run_id_obj.input_size)

        self.assertEqual(run_id['extraArgs'], run_id_obj.benchmark.extra_args)
        self.assertIsNone(run_id['extraArgs'])

        self.assertEqual(run_id['cores'], run_id_obj.cores)
        self.assertEqual(1, run_id['cores'])

        self.assertEqual(run_id['cmdline'], run_id_obj.cmdline())

    def _assert_benchmark_structure(self, run_id, run_id_obj):
        benchmark = run_id['benchmark']

        self.assertEqual(benchmark['name'], run_id_obj.benchmark.name)
        run_details = benchmark['runDetails']
        self.assertEqual(-1, run_details['maxInvocationTime'])
        self.assertEqual(50, run_details['minIterationTime'])
        self.assertIsNone(run_details['warmup'])

        suite = benchmark['suite']
        self.assertIsNone(suite['desc'])
        self.assertEqual('Suite', suite['name'])
        executor = suite['executor']
        self.assertIsNone(executor['desc'])
        self.assertEqual('TestRunner', executor['name'])

    def _assert_data_point_structure(self, data):
        self.assertEqual(10, len(data))
        for point, i in zip(data, list(range(0, 10))):
            self.assertEqual(1, point['in'])
            self.assertEqual(i + 1, point['it'])

            criteria = []
            if i % 2 == 0:
                criteria.append(0)
            if i % 3 == 0:
                criteria.append(1)
            if i % 2 == 1:
                criteria.append(3)
            criteria.append(2)

            for criterion, m in zip(criteria, point['m']):
                self.assertEqual(criterion, m['c'])
                self.assertEqual(i, int(m['v']))

    def _create_dummy_rebench_db_adapter(self):
        return ReBenchDB('http://localhost', '', '', self.ui)

    def test_data_conversion_to_rebench_db_api(self):
        cache, run_id_obj = self._run_exp_to_get_data_points_with_inconsistent_set_of_criteria()
        rebench_db = self._create_dummy_rebench_db_persistence()
        all_data, criteria_index, num_measurements = rebench_db.convert_data_to_api_format(cache)

        self.assertEqual(24, num_measurements)

        self._assert_criteria_index_structure(criteria_index)

        run_id = all_data[0]['runId']
        data = all_data[0]['d']

        self._assert_run_id_structure(run_id, run_id_obj)
        self._assert_benchmark_structure(run_id, run_id_obj)
        self._assert_data_point_structure(data)

        rdb = self._create_dummy_rebench_db_adapter()

        self.assertEqual('[{"in":1,"it":1,"m":[{"v":0.0,"c":0},{"v":0.0,"c":1},{"v":0.0,"c":2}]},' +
                         '{"in":1,"it":2,"m":[{"v":1.1,"c":3},{"v":1.1,"c":2}]},' +
                         '{"in":1,"it":3,"m":[{"v":2.2,"c":0},{"v":2.2,"c":2}]},' +
                         '{"in":1,"it":4,"m":[{"v":3.3,"c":1},{"v":3.3,"c":3},{"v":3.3,"c":2}]},' +
                         '{"in":1,"it":5,"m":[{"v":4.4,"c":0},{"v":4.4,"c":2}]},' +
                         '{"in":1,"it":6,"m":[{"v":5.5,"c":3},{"v":5.5,"c":2}]},' +
                         '{"in":1,"it":7,"m":[{"v":6.6,"c":0},{"v":6.6,"c":1},{"v":6.6,"c":2}]},' +
                         '{"in":1,"it":8,"m":[{"v":7.7,"c":3},{"v":7.7,"c":2}]},' +
                         '{"in":1,"it":9,"m":[{"v":8.8,"c":0},{"v":8.8,"c":2}]},' +
                         '{"in":1,"it":10,"m":[{"v":9.9,"c":1},{"v":9.9,"c":3},{"v":9.9,"c":2}]}]',
                         rdb.convert_data_to_json(data))

    def _assert_data_point_structure_v20(self, data):
        self.assertEqual(1, len(data))
        in1 = data[0]
        self.assertEqual(1, in1['in'])
        self.assertEqual(4, len(in1['m']))  # 4 criteria

        ms = in1['m']
        for i in range(0, 10):
            if i % 2 == 0:
                self.assertEqual(i, int(ms[0][i]))
            elif len(ms[0]) > i:
                self.assertIsNone(ms[0][i])

            if i % 3 == 0:
                self.assertEqual(i, int(ms[1][i]))
            elif len(ms[1]) > i:
                self.assertIsNone(ms[1][i])

            self.assertEqual(i, int(ms[2][i]))

            if i % 2 == 1:
                self.assertEqual(i, int(ms[3][i]))
            elif len(ms[3]) > i:
                self.assertIsNone(ms[3][i])

    def test_data_conversion_to_rebench_db_api_v20(self):
        cache, run_id_obj = self._run_exp_to_get_data_points_with_inconsistent_set_of_criteria()
        rebench_db = self._create_dummy_rebench_db_persistence()
        all_data, criteria_index, num_measurements = rebench_db.convert_data_to_api_20_format(cache)

        self.assertEqual(24, num_measurements)

        run_id = all_data[0]['runId']
        data = all_data[0]['d']

        self._assert_criteria_index_structure(criteria_index)
        self._assert_run_id_structure(run_id, run_id_obj)
        self._assert_benchmark_structure(run_id, run_id_obj)
        self._assert_data_point_structure_v20(data)

        rdb = self._create_dummy_rebench_db_adapter()
        self.assertEqual('[{"in":1,"m":[[0.0,null,2.2,null,4.4,null,6.6,null,8.8],' +
                         '[0.0,null,null,3.3,null,null,6.6,null,null,9.9],' +
                         '[0.0,1.1,2.2,3.3,4.4,5.5,6.6,7.7,8.8,9.9],' +
                         '[null,1.1,null,3.3,null,5.5,null,7.7,null,9.9]]}]',
                         rdb.convert_data_to_json(data))
