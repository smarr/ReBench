# Copyright (c) 2009-2013 Tobias Pape
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
import types
import tempfile
import os

from ..performance import StatsPerformance
from ..DataAggregator import DataAggregator, DataPoint, NonTimeDataPoint
from .. import ReBench
from ..Configurator import Configurator
from ..Executor import Executor
from ..Reporter import Reporters



# class StatsPerformanceIntegrationTest(unittest.TestCase):
#     """StatsPerfomance verifies the proper support for the
#        ReBenchConsoleResultProcessor output produced by
#        the Caliper version hosted at:

#          https://github.com/smarr/caliper

#        The test relies on pre-generated example data, but
#        covers the whole process of benchmarking, including
#        execution, and result parsing.
#     """

#     def setUp(self):
#         self._tmpFile = tempfile.mkstemp()[1] # just use the file name

#         self._path = os.path.dirname(os.path.realpath(__file__))
#         self._cwd  = os.getcwd()
#         os.chdir(self._path + '/../')


#     def tearDown(self):
#         os.remove(self._tmpFile)
#         os.chdir(self._cwd)


#     # Integration Test
#     def testFullExecution(self):
#         ## assert for the expected measurements as results
#         ## test for the expected number of executions of the
#         ## caliper runner
#         options = ReBench().shell_options().parse_args([])[0]

#         cnf  = Configurator(self._path + '/test.conf', options, 'TestCaliper')
#         data = DataAggregator(self._tmpFile)

#         ex = Executor(cnf, data, Reporters([]))
#         ex.execute()

#     def testCorrectNumberOfResultsFromRun(self):
#         ## Make sure that ReBench understands that a single
#         ## execution can return multiple results
#         ## Normally that should already be there...
#         pass


class StatsPerformanceReaderTest(unittest.TestCase):
    """ test the parser for correctly understanding the
        caliper output
    """

    def setUp(self):
        self._path = os.path.dirname(os.path.realpath(__file__))
        self._result1 = \
r"""Stats{
B:reverse:
C:shapes: 243
C:transformationrules: 133
N:iterations: 10
Ts:total: 2.8009698391
Ts:cpu: 2.776338
}Stats
"""
        with open(self._path + '/stats-out.txt', 'r') as f:
            self._result2 = f.read()
        self._c = StatsPerformance()

    def assertIsProperTupleWithTotal(self, expected_total, aTuple):
        self.assertIsInstance(aTuple, types.TupleType)
        self.assertEqual(2, len(aTuple))

        self.assertAlmostEqual(expected_total, aTuple[0])

        self.assertIsInstance(aTuple[1], types.ListType)

        self.assertGreaterEqual(len(aTuple[1]), 1)
        self.assertIsInstance(aTuple[1][0], DataPoint)

    def test_unmodified_command(self):

        cmd = ""
        self.assertEqual(cmd, self._c.acquire_command(cmd))

        cmd = "foobar"
        self.assertEqual(cmd, self._c.acquire_command(cmd))

        cmd = "  foo barr  "
        self.assertEqual(cmd, self._c.acquire_command(cmd))

    def test_parse_just_stats(self):
        parsed = self._c.parse_data(self._result1)
        total = 2.8009698391 / (1000 * 10)
        self.assertIsProperTupleWithTotal(total, parsed)

        data_point = parsed[1][0]
        self.assertIsInstance(data_point, NonTimeDataPoint)
        self.assertEqual("shapes", data_point.criterion)
        self.assertEqual(243, data_point.data)


        data_point = parsed[1][1]
        self.assertIsInstance(data_point, NonTimeDataPoint)
        self.assertEqual("transformationrules", data_point.criterion)
        self.assertEqual(133, data_point.data)

        data_point = parsed[1][2]
        self.assertEqual("total", data_point.criterion)
        self.assertAlmostEqual(total, data_point.time)

        cpu = 2.776338 / (1000 * 10)
        data_point = parsed[1][3]
        self.assertEqual("cpu", data_point.criterion)
        self.assertAlmostEqual(cpu, data_point.time)

    def test_parse_also_junk(self):
        parsed = self._c.parse_data(self._result2)
        total = 0.265885 / (1000 * 10)
        self.assertIsProperTupleWithTotal(total, parsed)

        data_point = parsed[1][0]
        self.assertIsInstance(data_point, NonTimeDataPoint)
        self.assertEqual("shapes", data_point.criterion)
        self.assertEqual(190, data_point.data)


        data_point = parsed[1][1]
        self.assertIsInstance(data_point, NonTimeDataPoint)
        self.assertEqual("transformationrules", data_point.criterion)
        self.assertEqual(29, data_point.data)

        data_point = parsed[1][2]
        self.assertEqual("total", data_point.criterion)
        self.assertAlmostEqual(total, data_point.time)

        cpu = 0.233144 / (1000 * 10)
        data_point = parsed[1][3]
        self.assertEqual("cpu", data_point.criterion)
        self.assertAlmostEqual(cpu, data_point.time)
