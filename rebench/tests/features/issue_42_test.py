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
from __future__ import print_function
import os
import unittest

from ...configurator import Configurator, load_config
from ...executor import Executor
from ...persistence import DataStore
from ..rebench_test_case import ReBenchTestCase


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


    def test_build_with_env_but_build_env_should_be_empty(self):
        cnf = Configurator(load_config(self._path + '/issue_42.conf'), DataStore(self.ui),
                           self.ui, data_file=self._tmp_file, exp_name='BuildWithEnv')
        runs = list(cnf.get_runs())
        runs = sorted(runs, key=lambda e: e.benchmark.name)

        ex = Executor(runs, True, self.ui, build_log=cnf.build_log)
        ex.execute()

        log = self._read_log()
        parts = log.split('|', 2)
        self.assertEqual("E:exe-with-build-and-env", parts[0])

        self._assert_empty_standard_env(parts[1])


    def test_build_without_env_and_build_env_should_be_empty(self):
        cnf = Configurator(load_config(self._path + '/issue_42.conf'), DataStore(self.ui),
                           self.ui, data_file=self._tmp_file, exp_name='BuildWithoutEnv')
        runs = list(cnf.get_runs())
        runs = sorted(runs, key=lambda e: e.benchmark.name)

        ex = Executor(runs, True, self.ui, build_log=cnf.build_log)
        ex.execute()

        log = self._read_log()
        parts = log.split('|', 2)
        self.assertEqual("E:exe-with-build-but-not-env", parts[0])
        self._assert_empty_standard_env(parts[1])


    def _assert_empty_standard_env(self, log_remainder):
        env_parts = log_remainder.split(':')
        self.assertEqual("STD", env_parts[0])

        env = sorted(env_parts[1].split('\n'))
        self.assertEqual('', env[0])
        self.assertTrue(env[1].startswith("PWD="))
        if len(env) > 2:
            self.assertEqual("SHLVL=1", env[2])
            self.assertEqual("_=/usr/bin/env", env[3])


if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')
