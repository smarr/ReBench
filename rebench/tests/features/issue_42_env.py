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

from ...configurator     import Configurator, load_config
from ...executor         import Executor
from ...persistence      import DataStore
from ..rebench_test_case import ReBenchTestCase


class Issue42BuildExecutor(ReBenchTestCase):

    def setUp(self):
        super(Issue42BuildExecutor, self).setUp()
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

    def test_build_executor_simple_cmd(self):
        cnf = Configurator(load_config(self._path + '/issue_42.conf'), DataStore(self.ui), self.ui)
        runs = list(cnf.get_runs())
        # runs = sorted(runs, key=lambda e: e.benchmark.name)
        #
        # ex = Executor(runs, True, self.ui, build_log=cnf.build_log)
        # ex.execute()
        #
        # try:
        #     self.assertEqual("Bench1", runs[0].benchmark.name)
        #     self.assertEqual(10, runs[0].get_number_of_data_points())
        #     self.assertTrue(os.path.isfile(self._path + '/vm_58a.sh'))
        # finally:
        #     os.remove(self._path + '/vm_58a.sh')


if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')