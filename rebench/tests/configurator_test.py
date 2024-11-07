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

from ..configurator     import Configurator, load_config, validate_gauge_adapters
from ..persistence      import DataStore
from ..output           import UIError
from .rebench_test_case import ReBenchTestCase


class ConfiguratorTest(ReBenchTestCase):

    def setUp(self):
        super(ConfiguratorTest, self).setUp()
        self._set_path(__file__)

    def test_experiment_name_from_cli(self):
        cnf = Configurator(load_config(self._path + '/test.conf'),
                           DataStore(self.ui), self.ui, None, 'Test')

        self.assertEqual("Test", cnf.experiment_name)

    def test_experiment_name_from_config_file(self):
        cnf = Configurator(load_config(self._path + '/test.conf'), DataStore(self.ui),
                           self.ui, None)
        self.assertEqual('Test', cnf.experiment_name)

    def test_number_of_experiments_smallconf(self):
        cnf = Configurator(load_config(self._path + '/small.conf'), DataStore(self.ui),
                           self.ui, None)
        self.assertEqual(1, len(cnf.get_experiments()))

    def test_number_of_experiments_testconf(self):
        cnf = Configurator(load_config(self._path + '/test.conf'), DataStore(self.ui),
                           self.ui, None, None, 'all')
        self.assertEqual(5, len(cnf.get_experiments()))
        self.assertEqual(53, len(cnf.get_runs()))

    def _get_experiment(self):
        cnf = Configurator(load_config(self._path + '/small.conf'), DataStore(self.ui),
                           self.ui, None)
        exp = cnf.get_experiment('Test')
        self.assertIsNotNone(exp)
        return exp

    def test_get_runs(self):
        exp = self._get_experiment()
        runs = exp.runs
        self.assertEqual(2 * 2 * 2, len(runs))

    # Support for running a selected experiment
    def test_only_running_test_runner2(self):
        filter_args = ['e:TestRunner2']
        cnf = Configurator(load_config(self._path + '/small.conf'), DataStore(self.ui),
                           self.ui, run_filter=filter_args)
        runs = cnf.get_runs()
        self.assertEqual(2 * 2, len(runs))

    def test_only_running_bench1(self):
        filter_args = ['s:Suite:Bench1']
        cnf = Configurator(load_config(self._path + '/small.conf'), DataStore(self.ui),
                           self.ui, run_filter=filter_args)

        runs = cnf.get_runs()
        self.assertEqual(2 * 2, len(runs))

    def test_star_filter_for_suite(self):
        filter_args = ['s:*:Bench1']
        cnf = Configurator(load_config(self._path + '/test.conf'), DataStore(self.ui),
                           self.ui, run_filter=filter_args)

        runs = cnf.get_runs()
        self.assertEqual(20, len(runs))

    def test_only_running_non_existing_stuff(self):
        filter_args = ['s:non-existing', 'e:non-existing']
        cnf = Configurator(load_config(self._path + '/small.conf'), DataStore(self.ui),
                           self.ui, run_filter=filter_args)

        runs = cnf.get_runs()
        self.assertEqual(0, len(runs))

    def test_only_running_bench1_and_test_runner2(self):
        filter_args = ['s:Suite:Bench1', 'e:TestRunner2']
        cnf = Configurator(load_config(self._path + '/small.conf'), DataStore(self.ui),
                           self.ui, run_filter=filter_args)

        runs = cnf.get_runs()
        self.assertEqual(2, len(runs))

    def test_only_running_bench1_or_bench2_and_test_runner2(self):
        filter_args = ['s:Suite:Bench1', 's:Suite:Bench2', 'e:TestRunner2']
        cnf = Configurator(load_config(self._path + '/small.conf'), DataStore(self.ui),
                           self.ui, run_filter=filter_args)

        runs = cnf.get_runs()
        self.assertEqual(2 * 2, len(runs))

    def test_tag_filter_m1(self):
        filter_args = ['t:machine1']
        cnf = Configurator(load_config(self._path + '/test.conf'), DataStore(self.ui),
                           self.ui, run_filter=filter_args)

        runs = cnf.get_runs()
        self.assertEqual(24, len(runs))

    def test_tag_filter_m2(self):
        filter_args = ['t:machine2']
        cnf = Configurator(load_config(self._path + '/test.conf'), DataStore(self.ui),
                           self.ui, run_filter=filter_args)

        runs = cnf.get_runs()
        self.assertEqual(16, len(runs))

    def test_tag_filter_m1_and_m2(self):
        filter_args = ['t:machine1', 't:machine2']
        cnf = Configurator(load_config(self._path + '/test.conf'), DataStore(self.ui),
                           self.ui, run_filter=filter_args)

        runs = cnf.get_runs()
        self.assertEqual(16 + 24, len(runs))

    def test_validate_gauge_adapters_with_all_correct_settings(self):
        result = validate_gauge_adapters({
            'benchmark_suites': {
                'StandardOne': {
                    'gauge_adapter': 'ReBenchLog'
                },
                'SimpleCustomOne': {
                    'gauge_adapter': {
                        'MyClass': './my_class.py'
                    }
                }
            }
        })
        self.assertTrue(result)

    def test_validate_gauge_adapters_with_wrong_settings(self):
        with self.assertRaises(UIError) as ctx:
            validate_gauge_adapters({
                'benchmark_suites': {
                    'TwoAdapters': {
                        'gauge_adapter': {
                            'MyClass1': './my_class.py',
                            'MyClass2': './my_class.py',
                        }
                    }
                }
            })
            self.assertIn('exactly one', ctx.exception.message)

    def test_validate_gauge_adapter_with_invalid_value(self):
        with self.assertRaises(UIError) as ctx:
            validate_gauge_adapters({
                'benchmark_suites': {
                    'InvalidValue': {
                        'gauge_adapter': 42
                    }
                }
            })
            self.assertIn('must be a string or a dict', ctx.exception.message)


# allow command-line execution
def test_suite():
    unittest.defaultTestLoader.loadTestsFromTestCase(ConfiguratorTest)


if __name__ == "__main__":
    unittest.main(defaultTest="test_suite")
