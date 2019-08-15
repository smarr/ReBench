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
import subprocess
import os

from .persistence import TestPersistence
from .rebench_test_case import ReBenchTestCase
from ..rebench           import ReBench
from ..executor          import Executor
from ..configurator      import Configurator, load_config
from ..model.measurement import Measurement
from ..persistence       import DataStore
from ..ui import UIError, TestDummyUI


class ExecutorTest(ReBenchTestCase):

    def setUp(self):
        super(ExecutorTest, self).setUp()
        os.chdir(self._path + '/../')

    def test_setup_and_run_benchmark(self):
        # before executing the benchmark,
        # we override stuff in subprocess for testing
        old_popen = subprocess.Popen
        subprocess.Popen = Popen_override

        try:
            options = ReBench().shell_options().parse_args(['dummy'])

            cnf = Configurator(load_config(self._path + '/test.conf'), DataStore(self._ui),
                               self._ui, options,
                               None, 'Test', data_file=self._tmp_file)

            ex = Executor(cnf.get_runs(), cnf.use_nice, cnf.do_builds, TestDummyUI())
            ex.execute()
        finally:
            subprocess.Popen = old_popen

    def test_broken_command_format_with_ValueError(self):
        with self.assertRaises(UIError) as err:
            options = ReBench().shell_options().parse_args(['dummy'])
            cnf = Configurator(load_config(self._path + '/test.conf'),
                               DataStore(self._ui), self._ui, options,
                               None, 'TestBrokenCommandFormat',
                               data_file=self._tmp_file)
            ex = Executor(cnf.get_runs(), cnf.use_nice, cnf.do_builds, TestDummyUI())
            ex.execute()
        self.assertIsInstance(err.exception.source_exception, ValueError)

    def test_broken_command_format_with_TypeError(self):
        with self.assertRaises(UIError) as err:
            options = ReBench().shell_options().parse_args(['dummy'])
            cnf = Configurator(load_config(self._path + '/test.conf'),
                               DataStore(self._ui), self._ui, options,
                               None, 'TestBrokenCommandFormat2',
                               data_file=self._tmp_file)
            ex = Executor(cnf.get_runs(), cnf.use_nice, cnf.do_builds, TestDummyUI())
            ex.execute()
            self.assertIsInstance(err.exception.source_exception, TypeError)

    def _basic_execution(self, cnf):
        runs = cnf.get_runs()
        self.assertEqual(8, len(runs))

        runs = cnf.get_runs()
        persistence = TestPersistence()
        for run in runs:
            run.add_persistence(persistence)

        ex = Executor(runs, cnf.use_nice, cnf.do_builds, TestDummyUI())
        ex.execute()
        for run in runs:
            data_points = persistence.get_data_points(run)
            self.assertEqual(10, len(data_points))
            for data_point in data_points:
                measurements = data_point.get_measurements()
                self.assertEqual(4, len(measurements))
                self.assertIsInstance(measurements[0], Measurement)
                self.assertTrue(measurements[3].is_total())
                self.assertEqual(data_point.get_total_value(),
                                 measurements[3].value)

    def test_basic_execution(self):
        cnf = Configurator(load_config(self._path + '/small.conf'),
                           DataStore(self._ui), self._ui, None,
                           data_file=self._tmp_file)
        self._basic_execution(cnf)

    def test_basic_execution_with_magic_all(self):
        cnf = Configurator(load_config(self._path + '/small.conf'),
                           DataStore(self._ui), self._ui, None, None,
                           'all', data_file=self._tmp_file)
        self._basic_execution(cnf)

    def test_execution_with_quick_set(self):
        self._set_path(__file__)
        option_parser = ReBench().shell_options()
        cmd_config = option_parser.parse_args(['-S', '-q', 'persistency.conf'])
        self.assertTrue(cmd_config.quick)

        cnf = Configurator(load_config(self._path + '/persistency.conf'), DataStore(self._ui),
                           self._ui, cmd_config, data_file=self._tmp_file)
        runs = cnf.get_runs()
        self.assertEqual(1, len(runs))

        ex = Executor(runs, False, False, self._ui)
        ex.execute()
        run = list(runs)[0]

        self.assertEqual(1, run.get_number_of_data_points())

    def test_execution_with_invocation_and_iteration_set(self):
        self._set_path(__file__)
        option_parser = ReBench().shell_options()
        cmd_config = option_parser.parse_args(['-S', '-in=2', '-it=2', 'persistency.conf'])
        self.assertEqual(2, cmd_config.invocations)
        self.assertEqual(2, cmd_config.iterations)

        cnf = Configurator(load_config(self._path + '/persistency.conf'), DataStore(self._ui),
                           self._ui, cmd_config, data_file=self._tmp_file)
        runs = cnf.get_runs()
        self.assertEqual(1, len(runs))

        ex = Executor(runs, False, False, self._ui)
        ex.execute()
        run = list(runs)[0]

        self.assertEqual(2, run.get_number_of_data_points())

    def test_shell_options_without_filters(self):
        option_parser = ReBench().shell_options()
        args = option_parser.parse_args(['-d', '-v', 'some.conf'])
        self.assertEqual(args.exp_filter, [])

    def test_shell_options_with_filters(self):
        option_parser = ReBench().shell_options()
        args = option_parser.parse_args(['-d', '-v', 'some.conf', 'exp_name'])
        self.assertEqual(args.exp_filter, ['exp_name'])

    def test_shell_options_with_executor_filter(self):
        option_parser = ReBench().shell_options()
        args = option_parser.parse_args(['-d', '-v', 'some.conf', 'e:foo'])
        self.assertEqual(args.exp_filter, ['e:foo'])

    def test_determine_exp_name_and_filters_empty(self):
        empty = []
        exp_name, exp_filter = ReBench.determine_exp_name_and_filters(empty)
        self.assertEqual(exp_name, None)
        self.assertEqual(exp_filter, [])

    def test_determine_exp_name_and_filters_all(self):
        filters = ['all']
        exp_name, exp_filter = ReBench.determine_exp_name_and_filters(filters)
        self.assertEqual(exp_name, "all")
        self.assertEqual(exp_filter, [])

    def test_determine_exp_name_and_filters_some_name(self):
        filters = ['foo']
        exp_name, exp_filter = ReBench.determine_exp_name_and_filters(filters)
        self.assertEqual(exp_name, "foo")
        self.assertEqual(exp_filter, [])

    def test_determine_exp_name_and_filters_all_and_other(self):
        filters = ['all', 'e:bar', 's:b']
        exp_name, exp_filter = ReBench.determine_exp_name_and_filters(filters)
        self.assertEqual(exp_name, "all")
        self.assertEqual(exp_filter, ['e:bar', 's:b'])

    def test_determine_exp_name_and_filters_only_others(self):
        filters = ['e:bar', 's:b']
        exp_name, exp_filter = ReBench.determine_exp_name_and_filters(filters)
        self.assertEqual(exp_name, None)
        self.assertEqual(exp_filter, ['e:bar', 's:b'])


def Popen_override(cmdline, stdout, stdin=None, stderr=None, cwd=None, shell=None):  # pylint: disable=unused-argument
    class Popen(object):
        returncode = 0

        def __init__(self, args):
            self.args = args

        def communicate(self, *_args, **_kwargs):
            return "", b""

        def poll(self):
            return self.returncode

        def kill(self):
            pass

        def wait(self, **_kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, _type, _value, _traceback):
            pass

    return Popen(cmdline)


def test_suite():
    return unittest.makeSuite(ExecutorTest)


if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')
