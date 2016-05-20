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
from ...model.benchmark_config import BenchmarkConfig
from ...model.benchmark_suite  import BenchmarkSuite
from ...model.run_id           import RunId
from ...model.virtual_machine  import VirtualMachine
from ...persistence            import DataStore

class Issue4RunEquality(unittest.TestCase):

    def setUp(self):
        self._path = os.path.dirname(os.path.realpath(__file__))

    def _create_template_run_id(self):
        vm        = VirtualMachine("MyVM", None, {'path':   'foo_bar_path',
                                                  'binary': 'foo_bar_bin'},
                                   None, [1], None)
        suite     = BenchmarkSuite("MySuite", vm, {
            'benchmarks': [], 'gauge_adapter': '',
            'command': '%(benchmark)s %(cores)s %(input)s'})
        bench_cfg = BenchmarkConfig("TestBench", "TestBench", None, suite, vm,
                                    '3', 0, None, DataStore())
        return RunId(bench_cfg, 1, 2, None)

    def _create_hardcoded_run_id(self):
        vm        = VirtualMachine("MyVM", None, {'path':   'foo_bar_path',
                                                  'binary': 'foo_bar_bin'},
                                   None, [1], None)
        suite     = BenchmarkSuite("MySuite", vm, {
            'benchmarks': [], 'gauge_adapter': '',
            'command': '%(benchmark)s %(cores)s 2 3'})
        bench_cfg = BenchmarkConfig("TestBench", "TestBench", None, suite, vm,
                                    None, 0, None, DataStore())
        return RunId(bench_cfg, 1, None, None)

    def test_hardcoded_equals_template_constructed(self):
        hard_coded = self._create_hardcoded_run_id()
        template   = self._create_template_run_id()

        self.assertEquals(hard_coded.cmdline(), template.cmdline())
        self.assertEquals(hard_coded, template)
        self.assertTrue(hard_coded == template)
        self.assertFalse(hard_coded is template)

