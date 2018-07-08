# Copyright (c) 2018 Stefan Marr <http://www.stefan-marr.de/>
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

from ...configurator     import Configurator, load_config
from ...executor         import Executor
from ...persistence      import DataStore
from ..rebench_test_case import ReBenchTestCase


class Issue59BuildSuite(ReBenchTestCase):

    def setUp(self):
        super(Issue59BuildSuite, self).setUp()
        self._set_path(__file__)

    def test_build_suite1(self):
        cnf = Configurator(load_config(self._path + '/issue_59.conf'), DataStore(self._ui),
                           self._ui, data_file=self._tmp_file, exp_name='A')
        runs = list(cnf.get_runs())
        runs = sorted(runs, key=lambda e: e.benchmark.name)

        ex = Executor(runs, False, True, self._ui, build_log=cnf.build_log)
        ex.execute()

        try:
            self.assertEqual("Bench1", runs[0].benchmark.name)
            self.assertEqual(2, runs[0].get_number_of_data_points())
            self.assertTrue(os.path.isfile(self._path + '/issue_59_cnt'))
        finally:
            os.remove(self._path + '/issue_59_cnt')

    def test_build_suite_same_command_executed_once_only(self):
        cnf = Configurator(load_config(self._path + '/issue_59.conf'), DataStore(self._ui),
                           self._ui, data_file=self._tmp_file, exp_name='Test')
        runs = list(cnf.get_runs())
        runs = sorted(runs, key=lambda e: e.benchmark.name)

        ex = Executor(runs, False, True, self._ui, build_log=cnf.build_log)
        ex.execute()

        try:
            self.assertEqual("Bench1", runs[0].benchmark.name)
            self.assertEqual(2, runs[0].get_number_of_data_points())
            self.assertTrue(os.path.isfile(self._path + '/issue_59_cnt'))
            with open(self._path + '/issue_59_cnt', 'r') as build_cnt:
                content = build_cnt.read()
            self.assertEqual("I\n", content)
        finally:
            os.remove(self._path + '/issue_59_cnt')
