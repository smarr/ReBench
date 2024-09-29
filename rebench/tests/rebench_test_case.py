# Copyright (c) 2014 Stefan Marr <http://www.stefan-marr.de/>
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
import logging
import os
from os.path  import dirname, realpath

import sys
from unittest import TestCase
from tempfile import mkstemp
from ..environment import init_env_for_test
from ..ui  import TestDummyUI


class ReBenchTestCase(TestCase):

    def _set_path(self, path):
        self._path = dirname(realpath(path))
        os.chdir(self._path)
        init_env_for_test()

    def setUp(self):
        logging.getLogger("pykwalify").addHandler(logging.NullHandler())

        self._set_path(__file__)
        self._tmp_file = mkstemp()[1]  # just use the file name

        self._sys_exit = sys.exit  # make sure that we restore sys.exit
        self.ui = TestDummyUI()

    def tearDown(self):
        os.remove(self._tmp_file)
        sys.exit = self._sys_exit

    def _assert_runs(self, cnf, num_runs, num_dps, num_invocations):
        """
        :param cnf: Configurator
        :param num_runs: expected number of runs
        :param num_dps: expected number of data points
        :param num_invocations: expected number of invocations
        :return:
        """
        runs = cnf.get_runs()
        self.assertEqual(num_runs, len(runs), "incorrect number of runs")
        run = list(runs)[0]

        self.assertEqual(num_dps, run.get_number_of_data_points(), "incorrect num of data points")
        self.assertEqual(num_invocations, run.completed_invocations, "incorrect num of invocations")
