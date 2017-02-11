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
from ...configurator     import Configurator
from ...executor         import Executor
from ...persistence      import DataStore
from ..rebench_test_case import ReBenchTestCase

import os


class Issue58BuildVM(ReBenchTestCase):

    def setUp(self):
        super(Issue58BuildVM, self).setUp(__file__)

    def test_build_vm_simple_cmd(self):
        cnf = Configurator(self._path + '/issue_58.conf', DataStore(),
                           standard_data_file = self._tmp_file,
                           exp_name='A')
        runs = list(cnf.get_runs())
        runs = sorted(runs, key=lambda e: e.bench_cfg.name)

        ex = Executor(runs, False, False, build_log=cnf.build_log)
        ex.execute()

        self.assertEqual("Bench1", runs[0].bench_cfg.name)
        self.assertEqual(10, runs[0].get_number_of_data_points())
        self.assertTrue(os.path.isfile(self._path + '/vm_58a.sh'))
        os.remove(self._path + '/vm_58a.sh')

    def test_build_vm_cmd_list(self):
        cnf = Configurator(self._path + '/issue_58.conf', DataStore(),
                           standard_data_file = self._tmp_file,
                           exp_name='B')
        runs = list(cnf.get_runs())
        runs = sorted(runs, key=lambda e: e.bench_cfg.name)

        ex = Executor(runs, False, False, build_log=cnf.build_log)
        ex.execute()

        self.assertEqual("Bench1", runs[0].bench_cfg.name)
        self.assertEqual(10, runs[0].get_number_of_data_points())
        self.assertTrue(os.path.isfile(self._path + '/vm_58b.sh'))
        os.remove(self._path + '/vm_58b.sh')

    def test_build_output_in_log(self):
        if os.path.isfile(self._path + '/build.log'):
            os.remove(self._path + '/build.log')

        self.test_build_vm_simple_cmd()

        with open(self._path + '/build.log', 'r') as log_file:
            log = log_file.read()

        self.assertEqual(
            "BashA|STD:standard\nBashA|ERR:error\n\n", log)

    def test_broken_build_prevents_experiments(self):
        if os.path.isfile(self._path + '/build.log'):
            os.remove(self._path + '/build.log')
        cnf = Configurator(self._path + '/issue_58.conf', DataStore(),
                           standard_data_file=self._tmp_file,
                           exp_name='C')
        runs = list(cnf.get_runs())
        runs = sorted(runs, key=lambda e: e.bench_cfg.name)

        ex = Executor(runs, False, False, build_log=cnf.build_log)
        ex.execute()

        self.assertEqual("Bench1", runs[0].bench_cfg.name)
        self.assertEqual(0, runs[0].get_number_of_data_points())
        print self._path + '/vm_58a.sh'
        self.assertTrue(os.path.isfile(self._path + '/vm_58a.sh'))
        os.remove(self._path + '/vm_58a.sh')

        with open(self._path + '/build.log', 'r') as log_file:
            log = log_file.read()

        self.assertEqual(
            "BashC|STD:standard\nBashC|ERR:error\n\n", log)
