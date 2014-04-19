# Copyright (c) 2009-2014 Stefan Marr <http://www.stefan-marr.de/>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
import os
import unittest
import sys

from os.path import dirname, realpath
from tempfile import mkstemp

from ...configurator           import Configurator
from ...executor               import Executor

from ...model.benchmark_config import BenchmarkConfig
from ...model.run_id           import RunId
from ...persistence            import DataPointPersistence


class Issue27InvalidRunNotHandled(unittest.TestCase):

    def setUp(self):
        self._path     = dirname(realpath(__file__))
        self._tmp_file = mkstemp()[1]  # just use the file name

        BenchmarkConfig.reset()
        RunId.reset()
        DataPointPersistence.reset()

        self._sys_exit = sys.exit  # make sure that we restore sys.exit

        os.chdir(self._path)

    def test_execution_should_recognize_invalid_run_and_continue_normally(self):
        cnf = Configurator(self._path + '/issue_27.conf',
                           standard_data_file = self._tmp_file)
        runs = list(cnf.get_runs())
        self.assertEquals(runs[0].get_number_of_data_points(), 0)

        ex = Executor([runs[0]], False)
        ex.execute()

        self.assertEquals(runs[0].get_number_of_data_points(), 0)
