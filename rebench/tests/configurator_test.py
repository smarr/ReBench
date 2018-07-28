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
import unittest

from ..configurator           import Configurator, load_config
from ..persistence            import DataStore
from .rebench_test_case import ReBenchTestCase


class ConfiguratorTest(ReBenchTestCase):

    def test_experiment_name_from_cli(self):
        cnf = Configurator(load_config(self._path + '/test.conf'),
                           DataStore(self._ui), self._ui, None, 'Test')

        self.assertEqual('Test', cnf.experiment_name)

    def test_experiment_name_from_config_file(self):
        cnf = Configurator(load_config(self._path + '/test.conf'), DataStore(self._ui),
                           self._ui, None)
        self.assertEqual('Test', cnf.experiment_name)

    def test_number_of_experiments_smallconf(self):
        cnf = Configurator(load_config(self._path + '/small.conf'), DataStore(self._ui),
                           self._ui, None)
        self.assertEqual(1, len(cnf.get_experiments()))

    @unittest.skip
    def test_number_of_experiments_testconf(self):
        cnf = Configurator(load_config(self._path + '/test.conf'), DataStore(self._ui),
                           self._ui, None, None, 'all')
        self.assertEqual(6, len(cnf.get_experiments()))

    def test_get_experiment(self):
        cnf = Configurator(load_config(self._path + '/small.conf'), DataStore(self._ui),
                           self._ui, None)
        exp = cnf.get_experiment('Test')
        self.assertIsNotNone(exp)
        return exp

    def test_get_runs(self):
        exp = self.test_get_experiment()
        runs = exp.get_runs()
        self.assertEqual(2 * 2 * 2, len(runs))

    # Support for running a selected experiment
    def test_only_running_test_runner2(self):
        filter_args = ['e:TestRunner2']
        cnf = Configurator(load_config(self._path + '/small.conf'), DataStore(self._ui),
                           self._ui, run_filter=filter_args)
        runs = cnf.get_runs()
        self.assertEqual(2 * 2, len(runs))

    def test_only_running_bench1(self):
        filter_args = ['s:Suite:Bench1']
        cnf = Configurator(load_config(self._path + '/small.conf'), DataStore(self._ui),
                           self._ui, run_filter=filter_args)

        runs = cnf.get_runs()
        self.assertEqual(2 * 2, len(runs))

    def test_only_running_non_existing_stuff(self):
        filter_args = ['s:non-existing', 'e:non-existing']
        cnf = Configurator(load_config(self._path + '/small.conf'), DataStore(self._ui),
                           self._ui, run_filter=filter_args)

        runs = cnf.get_runs()
        self.assertEqual(0, len(runs))

    def test_only_running_bench1_and_test_runner2(self):
        filter_args = ['s:Suite:Bench1', 'e:TestRunner2']
        cnf = Configurator(load_config(self._path + '/small.conf'), DataStore(self._ui),
                           self._ui, run_filter=filter_args)

        runs = cnf.get_runs()
        self.assertEqual(2, len(runs))

    def test_only_running_bench1_or_bench2_and_test_runner2(self):
        filter_args = ['s:Suite:Bench1', 's:Suite:Bench2', 'e:TestRunner2']
        cnf = Configurator(load_config(self._path + '/small.conf'), DataStore(self._ui),
                           self._ui, run_filter=filter_args)

        runs = cnf.get_runs()
        self.assertEqual(2 * 2, len(runs))


# allow command-line execution
def test_suite():
    return unittest.makeSuite(ConfiguratorTest)


if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')
