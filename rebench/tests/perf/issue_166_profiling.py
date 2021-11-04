from ...configurator import Configurator, load_config
from ...persistence  import DataStore

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

    def test_send_to_rebench_db(self):
        # In the end, I want to be sure that the profiling data is sent to ReBenchDB
        pass

    def test_check_profile_in_separate_data_file(self):
        # I want to be sure the profiling data is stored in the data file (possibly a separate one)
        pass

    def test_perf_replacement_works(self):
        # I want to be able to execute the benchmarks without having to have perf or sudo rights or anything
        #   -> I want to be able to test this at least partially on macOS, where we don't have perf
        pass
