import json

from ...configurator import Configurator, load_config
from ...executor import Executor
from ...model.profile_data import ProfileData
from ...persistence import DataStore
from ...interop.perf_adapter import PerfAdapter

from ..rebench_test_case import ReBenchTestCase


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
        self.assertEqual(profiler.record_args, "record -g -F 9999 --call-graph lbr")
        self.assertEqual(profiler.report_args, "report -g graph --no-children --stdio")

        # TODO: how do we deal with having multiple profilers defined?
        # this is something for when we support more than one
        # perhaps it's a command line flag, or a setting of the experiment, ...
        # depends where we want to OS-dependent bits to come in...

    def test_send_to_rebench_db(self):
        # In the end, I want to be sure that the profiling data is sent to ReBenchDB
        self.fail("TODO")

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

        data_point = ProfileData(run_id, "TEST-DATA, not json though, just a string", 1, 1)
        run_id.add_data_point(data_point, True)
        run_id.close_files()
        self.assertEqual(1, run_id.completed_invocations)

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

    def test_perf_gauge_adapter_reads_perf_report(self):
        cnf = Configurator(load_config(self._path + '/issue_166.conf'), DataStore(self.ui),
                           self.ui, data_file=self._tmp_file)
        runs = list(cnf.get_runs())
        run_id = runs[0]

        self._make_profiler_return_small_report(run_id)

        perf_adapter = PerfAdapter()
        out_from_benchmark = ""  # don't really need it

        data = perf_adapter.parse_data(out_from_benchmark, run_id, 1)
        self.assertEqual(1, len(data))

        profile_data = data[0]
        self.assertEqual(1, profile_data.invocation)
        self.assertEqual(1, profile_data.num_iterations)
        self.assertIsNotNone(profile_data.processed_data)

        result_data = json.loads(profile_data.processed_data)
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

        self._make_profiler_return_small_report(run_id)

        executor = Executor(runs, False, self.ui)
        executor.execute()

        self.assertEqual(1, run_id.completed_invocations)

    @staticmethod
    def _make_profiler_return_small_report(run_id):
        # need first to mess with the profiler, to load our test data
        profilers = run_id.benchmark.suite.executor.profiler
        profiler = profilers[0]
        profiler.command = "./cat-first.sh"
        profiler.record_args = "perf-small.report"
        profiler.report_args = "perf-small.report"
