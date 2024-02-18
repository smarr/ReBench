from unittest import skipIf

from ..mock_http_server import MockHTTPServer
from ...configurator import Configurator, load_config
from ...environment import git_not_available, git_repo_not_initialized
from ...executor import Executor
from ...model.profile_data import ProfileData
from ...persistence import DataStore
from ...interop.perf_adapter import PerfAdapter

from ..rebench_test_case import ReBenchTestCase
from ...rebench import ReBench


class Issue166ProfilingSupportTest(ReBenchTestCase):
    def setUp(self):
        super(Issue166ProfilingSupportTest, self).setUp()
        self._set_path(__file__)

    def test_check_executors_raw_values(self):
        cnf = Configurator(load_config(self._path + '/issue_166.conf'), DataStore(self.ui),
                           self.ui, data_file=self._tmp_file)
        execs = cnf._executors

        self.assertEqual(2, len(execs))

        self.assertEqual(execs['TestRunner1']['profiler']['perf']['record_args'],
                         "record -g -F 9999 --call-graph lbr")
        self.assertEqual(execs['TestRunner1']['profiler']['perf']['report_args'],
                         "report -g graph --no-children --stdio")

        self.assertEqual(execs['TestRunner2']['profiler']['perf']['record_args'],
                         "record custom-args")
        self.assertEqual(execs['TestRunner2']['profiler']['perf']['report_args'],
                         "report custom-args")

    def test_run_id_includes_profiling_details(self):
        cnf = Configurator(load_config(self._path + '/issue_166.conf'), DataStore(self.ui),
                           self.ui, data_file=self._tmp_file)
        run_id = list(cnf.get_runs())[0]
        profilers = run_id.benchmark.suite.executor.profiler
        self.assertEqual(len(profilers), 1)

        profiler = profilers[0]

        self.assertEqual(profiler.name, "perf")
        self.assertEqual(profiler.command, "perf")
        self.assertEqual(profiler.record_args,
                         "record -g -F 9999 --call-graph lbr --output=profile.perf ")
        self.assertEqual(profiler.report_args,
                         "report -g graph --no-children --stdio --input=profile.perf ")

        # TODO: how do we deal with having multiple profilers defined?
        # this is something for when we support more than one
        # perhaps it's a command line flag, or a setting of the experiment, ...
        # depends where we want to OS-dependent bits to come in...

    def _load_config_and_use_tmp_as_data_file(self):
        raw_config = load_config(self._path + '/issue_166.conf')
        raw_config['experiments']['profile']['data_file'] = self._tmp_file
        return raw_config

    def test_persist_profile_data(self):
        raw_config = self._load_config_and_use_tmp_as_data_file()
        cnf = Configurator(raw_config, DataStore(self.ui), self.ui)
        runs = list(cnf.get_runs())
        run_id = runs[0]

        self.assertEqual(0, run_id.completed_invocations)
        self.assertEqual(0, run_id.get_number_of_data_points())

        data_point = ProfileData(run_id, "TEST-DATA, not json though, just a string", 1, 1)
        run_id.add_data_point(data_point, False)
        run_id.close_files()
        self.assertEqual(1, run_id.completed_invocations)
        self.assertEqual(1, run_id.get_number_of_data_points())

        # create new data store, and load data file
        data_store = DataStore(self.ui)
        cnf = Configurator(raw_config, data_store, self.ui)
        data_store.get(self._tmp_file, cnf, "profile")
        data_store.load_data(None, False)

        # confirm that data was loaded (we don't have direct access to it,
        # so, just check that completion count is correct)
        run_id2 = list(cnf.get_runs())[0]
        self.assertIsNot(run_id, run_id2)
        self.assertEqual(1, run_id2.completed_invocations)
        self.assertEqual(1, run_id2.get_number_of_data_points())

    def test_perf_gauge_adapter_reads_perf_report(self):
        cnf = Configurator(load_config(self._path + '/issue_166.conf'), DataStore(self.ui),
                           self.ui, data_file=self._tmp_file)
        runs = list(cnf.get_runs())
        run_id = runs[0]

        self._make_profiler_return_small_report(run_id)

        executor = Executor(runs, False, self.ui)
        executor.use_denoise = False

        perf_adapter = PerfAdapter(False, executor)
        out_from_benchmark = ""  # don't really need it

        data = perf_adapter.parse_data(out_from_benchmark, run_id, 1)
        self.assertEqual(1, len(data))

        profile_data = data[0]
        self.assertEqual(1, profile_data.invocation)
        self.assertEqual(1, profile_data.num_iterations)
        self.assertIsNotNone(profile_data.processed_data)

        result_data = profile_data.processed_data
        self.assertEqual(len(result_data), 10)

        self.assertEqual(
            'MessageSendNode$AbstractMessageSendNode_evaluateArguments', result_data[0]['m'])
        self.assertEqual('intel_pmu_handle_irq', result_data[9]['m'])

    def test_execute_profiling(self):
        raw_config = self._load_config_and_use_tmp_as_data_file()
        cnf = Configurator(raw_config, DataStore(self.ui), self.ui, data_file=self._tmp_file)
        runs = cnf.get_runs()
        run_id = list(cnf.get_runs())[0]
        self.assertEqual(0, run_id.completed_invocations)
        self.assertEqual(0, run_id.get_number_of_data_points())

        self._make_profiler_return_small_report(run_id)

        executor = Executor(runs, False, self.ui)
        executor.execute()

        self.assertEqual(1, run_id.completed_invocations)
        self.assertEqual(1, run_id.get_number_of_data_points())

    def test_execute_profiling_profile2(self):
        raw_config = self._load_config_and_use_tmp_as_data_file()
        cnf = Configurator(
            raw_config, DataStore(self.ui), self.ui, exp_name="profile2", data_file=self._tmp_file)

        runs = cnf.get_runs()
        run_id = list(cnf.get_runs())[0]
        self.assertEqual(0, run_id.completed_invocations)
        self.assertEqual(0, run_id.get_number_of_data_points())

        self._make_profiler_return_small_report(run_id)

        executor = Executor(runs, False, self.ui)
        executor.execute()

        self.assertEqual(7, run_id.completed_invocations)
        self.assertEqual(7, run_id.get_number_of_data_points())

    @skipIf(git_not_available() or git_repo_not_initialized(),
        "git source info not available, but needed for reporting to ReBenchDB")
    def test_send_to_rebench_db(self):
        server = MockHTTPServer()
        port = server.get_free_port()
        server.start()

        raw_config = self._load_config_and_use_tmp_as_data_file()
        raw_config['reporting'] = {}
        raw_config['reporting']['rebenchdb'] = {
            'db_url': 'http://localhost:' + str(port),
            'repo_url': 'http://repo.git',
            'project_name': 'Persistency Test',
            'send_to_rebench_db': True,
            'record_all': True}

        option_parser = ReBench().shell_options()
        cmd_config = option_parser.parse_args(['--experiment=Test', 'ignored'])

        try:
            cnf = Configurator(
                raw_config, DataStore(self.ui), self.ui, cmd_config, data_file=self._tmp_file)
            runs = cnf.get_runs()
            run_id = list(cnf.get_runs())[0]
            self._make_profiler_return_small_report(run_id)

            executor = Executor(runs, False, self.ui)
            executor.execute()

            run_id.close_files()

            self.assertEqual(1, run_id.completed_invocations)
            self.assertEqual(1, run_id.get_number_of_data_points())

            server.process_and_shutdown()

            self.assertEqual(1, server.get_number_of_put_requests())
        finally:
            server.process_and_shutdown()

    @staticmethod
    def _make_profiler_return_small_report(run_id):
        # need first to mess with the profiler, to load our test data
        profilers = run_id.benchmark.suite.executor.profiler
        profiler = profilers[0]
        profiler.command = "./cat-first.sh"
        profiler.record_args = "perf-small.report"
        profiler.report_args = "perf-small.report"
