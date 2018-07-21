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
from ...model.benchmark import Benchmark
from ...model.benchmark_suite  import BenchmarkSuite
from ...model.run_id           import RunId
from ...model.exp_run_details  import ExpRunDetails
from ...model.executor  import Executor
from ...persistence            import DataStore
from ...ui                     import TestDummyUI


class Issue4RunEquality(unittest.TestCase):

    def setUp(self):
        self._path = os.path.dirname(os.path.realpath(__file__))

    @staticmethod
    def _create_template_run_id():
        executor = Executor('MyVM', 'foo_bar_path', 'foo_bar_bin',
                            None, None, None, None, None)
        suite = BenchmarkSuite("MySuite", executor, '', '%(benchmark)s %(cores)s %(input)s',
                               None, None, [], None, None, None)
        benchmark = Benchmark("TestBench", "TestBench", None, suite, None,
                              '3', ExpRunDetails.empty(), None, DataStore(TestDummyUI()))
        return RunId(benchmark, 1, 2, None)

    @staticmethod
    def _create_hardcoded_run_id():
        executor = Executor('MyVM', 'foo_bar_path', 'foo_bar_bin',
                            None, None, None, None, None)
        suite = BenchmarkSuite('MySuite', executor, '', '%(benchmark)s %(cores)s 2 3',
                               None, None, [], None, None, None)
        benchmark = Benchmark("TestBench", "TestBench", None, suite,
                              None, None, ExpRunDetails.empty(), None, DataStore(TestDummyUI()))
        return RunId(benchmark, 1, None, None)

    def test_hardcoded_equals_template_constructed(self):
        hard_coded = self._create_hardcoded_run_id()
        template = self._create_template_run_id()

        self.assertEqual(hard_coded.cmdline(), template.cmdline())
        self.assertEqual(hard_coded, template)
        self.assertTrue(hard_coded == template)
        self.assertFalse(hard_coded is template)
