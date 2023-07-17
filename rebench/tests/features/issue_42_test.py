# Copyright (c) 2017 Stefan Marr <http://www.stefan-marr.de/>
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
import os
import unittest
from unittest import skip

from ...configurator import Configurator, load_config
from ...executor import Executor
from ...interop.time_adapter import TimeManualAdapter
from ...persistence import DataStore
from ...reporter import Reporter
from ..rebench_test_case import ReBenchTestCase


class _TestFailedReporter(Reporter):

    def __init__(self):
        super(_TestFailedReporter, self).__init__()
        self.output = None

    def run_failed(self, _run_id, _cmdline, _return_code, output):
        self.output = output


class Issue42SupportForEnvironmentVariables(ReBenchTestCase):

    def setUp(self):
        super(Issue42SupportForEnvironmentVariables, self).setUp()
        self._set_path(__file__)
        self._cleanup_log()

    def tearDown(self):
        self._cleanup_log()

    def _cleanup_log(self):
        if os.path.isfile(self._path + '/build.log'):
            os.remove(self._path + '/build.log')

    def _read_log(self):
        # pylint: disable-next=unspecified-encoding
        with open(self._path + '/build.log', 'r') as log_file:
            return log_file.read()

    def test_env_vars_are_set_as_expected(self):
        cnf = Configurator(load_config(self._path + '/issue_42.conf'), DataStore(self.ui),
                           self.ui, data_file=self._tmp_file, exp_name='test-set-as-expected')
        runs = list(cnf.get_runs())
        reporter = _TestFailedReporter()
        runs[0].add_reporter(reporter)

        ex = Executor(runs, True, self.ui, build_log=cnf.build_log)
        succeeded = ex.execute()
        if not succeeded:
            print(reporter.output)
        self.assertTrue(succeeded)

        self.assertEqual("as-expected", runs[0].benchmark.name)
        self.assertFalse(runs[0].is_failed)

    def test_run_without_config_has_empty_env(self):
        cnf = Configurator(load_config(self._path + '/issue_42.conf'), DataStore(self.ui),
                           self.ui, data_file=self._tmp_file, exp_name='test-no-env')
        runs = list(cnf.get_runs())
        reporter = _TestFailedReporter()
        runs[0].add_reporter(reporter)

        ex = Executor(runs, True, self.ui, build_log=cnf.build_log)
        succeeded = ex.execute()
        if not succeeded:
            print(reporter.output)
        self.assertTrue(succeeded)

        self.assertEqual("no-env", runs[0].benchmark.name)
        self.assertFalse(runs[0].is_failed)

    def test_build_with_env_should_see_a_run_env(self):
        cnf = Configurator(load_config(self._path + '/issue_42.conf'), DataStore(self.ui),
                           self.ui, data_file=self._tmp_file, exp_name='build-with-env')
        runs = list(cnf.get_runs())
        runs = sorted(runs, key=lambda e: e.benchmark.name)

        ex = Executor(runs, True, self.ui, build_log=cnf.build_log)
        ex.execute()

        log = self._read_log()
        parts = log.split('|', 2)
        self.assertEqual("E:exe-with-build-and-env", parts[0])

        env_parts = parts[1].split(':')
        env = sorted(env_parts[1].split('\n'))
        self.assertEqual('', env[0])
        self.assertTrue(env[1].startswith("PWD="))
        if env[2].startswith("SHLVL"):  # Platform differences
            self.assertEqual("SHLVL=1", env[2])
            self.assertEqual("VAR1=test", env[3])
            self.assertEqual("VAR3=another test", env[4])
            self.assertTrue(env[5].startswith("_="))
        else:
            self.assertEqual("VAR1=test", env[2])
            self.assertEqual("VAR3=another test", env[3])

    def test_build_and_run_without_env_should_have_empty_env(self):
        cnf = Configurator(load_config(self._path + '/issue_42.conf'), DataStore(self.ui),
                           self.ui, data_file=self._tmp_file, exp_name='build-without-env')
        runs = list(cnf.get_runs())
        runs = sorted(runs, key=lambda e: e.benchmark.name)

        ex = Executor(runs, True, self.ui, build_log=cnf.build_log)
        ex.execute()

        log = self._read_log()
        parts = log.split('|', 2)
        self.assertEqual("E:exe-with-build-but-not-env", parts[0])
        self._assert_empty_standard_env(parts[1])

    def test_construct_cmdline_env_vars_set_as_expected(self):
        cnf = Configurator(load_config(self._path + '/issue_42.conf'), DataStore(self.ui),
                           self.ui, data_file=self._tmp_file, exp_name='test-set-as-expected')
        runs = list(cnf.get_runs())
        ex = Executor(runs, True, self.ui, use_nice=True, use_shielding=True)

        self.assertIn(" --preserve-env=IMPORTANT_ENV_VARIABLE,ALSO_IMPORTANT rebench-denoise",
                      ex._construct_cmdline(runs[0], TimeManualAdapter(False, ex)))

    def test_construct_cmdline_build_with_env(self):
        cnf = Configurator(load_config(self._path + '/issue_42.conf'), DataStore(self.ui),
                           self.ui, data_file=self._tmp_file, exp_name='build-with-env')
        runs = list(cnf.get_runs())
        ex = Executor(runs, True, self.ui, use_nice=True, use_shielding=True)

        self.assertIn(" --preserve-env=VAR1,VAR3 rebench-denoise",
                      ex._construct_cmdline(runs[0], TimeManualAdapter(False, ex)))

    def _assert_empty_standard_env(self, log_remainder):
        env_parts = log_remainder.split(':')
        self.assertEqual("STD", env_parts[0])

        env = sorted(env_parts[1].split('\n'))
        self.assertEqual('', env[0])
        self.assertTrue(env[1].startswith("PWD="))
        if len(env) > 2:
            self.assertEqual("SHLVL=1", env[2])
            self.assertEqual("_=/usr/bin/env", env[3])

    @skip("Needs more work, left here for documentation")
    def test_env_supports_value_expansion(self):
        cnf = Configurator(load_config(self._path + '/issue_42.conf'), DataStore(self.ui),
                           self.ui, data_file=self._tmp_file, exp_name='test-value-expansion')
        runs = list(cnf.get_runs())
        runs = sorted(runs, key=lambda e: e.benchmark.name)

        ex = Executor(runs, True, self.ui, build_log=cnf.build_log)
        ex.execute()
        # TODO: before this can work, we need to be able to consider env as part of the run id,
        # which sounds like a major change...
        # the variable replacement is also not yet implemented for env vars
        # should probably be done at the same time the commandline is constructed
        # runs
        # TODO: assert that the result values for the runs are matching
        # the input size given in the env var.


if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')
