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
from .rebench_test_case import ReBenchTestCase

from ..persistence import DataStore

from ..configurator import Configurator, load_config
from ..executor import Executor
from ..model.benchmark import Benchmark
from ..model.benchmark_suite import BenchmarkSuite
from ..model.executor import Executor as ExecutorConf
from ..model.exp_run_details import ExpRunDetails
from ..model.measurement import Measurement
from ..model.run_id import RunId


class PersistencyTest(ReBenchTestCase):

    def test_de_serialization(self):
        data_store = DataStore(self._ui)
        executor = ExecutorConf("MyVM", '', '',
                                None, None, None, None, None)
        suite = BenchmarkSuite("MySuite", executor, '', '', None, None,
                               None, None, None, None)
        benchmark = Benchmark("Test Bench [>", "Test Bench [>", None,
                              suite, None, None, ExpRunDetails.default(None, None),
                              None, data_store)

        run_id = RunId(benchmark, 1000, 44, 'sdf sdf sdf sdfsf')
        measurement = Measurement(43, 45, 2222.2222, 'ms', run_id, 'foobar crit')

        serialized = measurement.as_str_list()
        deserialized = Measurement.from_str_list(data_store, serialized)

        self.assertEqual(deserialized.criterion, measurement.criterion)
        self.assertEqual(deserialized.value, measurement.value)
        self.assertEqual(deserialized.unit, measurement.unit)
        self.assertEqual(deserialized.invocation, measurement.invocation)
        self.assertEqual(deserialized.iteration, measurement.iteration)

        self.assertEqual(deserialized.run_id, measurement.run_id)

    def _assert_runs(self, cnf, num_runs, num_dps, num_invocations):
        runs = cnf.get_runs()
        self.assertEqual(num_runs, len(runs))
        run = list(runs)[0]

        self.assertEqual(num_dps, run.get_number_of_data_points())
        self.assertEqual(num_invocations, run.completed_invocations)

    def test_iteration_invocation_semantics(self):
        # Executes first time
        ds = DataStore(self._ui)
        cnf = Configurator(load_config(self._path + '/persistency.conf'),
                           ds, self._ui, data_file=self._tmp_file)
        ds.load_data(None, False)

        self._assert_runs(cnf, 1, 0, 0)

        ex = Executor(cnf.get_runs(), False, False, self._ui)
        ex.execute()

        self._assert_runs(cnf, 1, 10, 10)

        # Execute a second time, should not add any data points,
        # because goal is already reached
        ds2 = DataStore(self._ui)
        cnf2 = Configurator(load_config(self._path + '/persistency.conf'),
                            ds2, self._ui, data_file=self._tmp_file)
        ds2.load_data(None, False)

        self._assert_runs(cnf2, 1, 10, 10)

        ex2 = Executor(cnf2.get_runs(), False, False, self._ui)
        ex2.execute()

        self._assert_runs(cnf2, 1, 10, 10)

    def test_data_discarding(self):
        # Executes first time
        ds = DataStore(self._ui)
        cnf = Configurator(load_config(self._path + '/persistency.conf'),
                           ds, self._ui, data_file=self._tmp_file)
        ds.load_data(None, False)

        self._assert_runs(cnf, 1, 0, 0)

        ex = Executor(cnf.get_runs(), False, False, self._ui)
        ex.execute()

        self._assert_runs(cnf, 1, 10, 10)

        # Execute a second time, this time, discard the data first, and then rerun
        ds2 = DataStore(self._ui)
        cnf2 = Configurator(load_config(self._path + '/persistency.conf'),
                            ds2, self._ui, data_file=self._tmp_file)
        run2 = cnf2.get_runs()
        ds2.load_data(run2, True)

        self._assert_runs(cnf2, 1, 0, 0)

        ex2 = Executor(run2, False, False, self._ui)
        ex2.execute()

        self._assert_runs(cnf2, 1, 10, 10)
