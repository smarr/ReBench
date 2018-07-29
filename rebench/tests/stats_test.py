# Copyright (c) 2009-2014 Stefan Marr <http://www.stefan-marr.de/>
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
from ..statistics import StatisticProperties


class StatsTest(unittest.TestCase):

    def setUp(self):
        self._integers = list(range(1, 50))
        self._floats = [float(x) for x in self._integers]
        self._floats2 = [float(x) + 2.31 for x in self._integers]

        self._mixed = [x if x % 2 == 0 else float(x) + 4.5
                       for x in self._integers]

    def _assert(self, stats, mean_val, geo_mean, min_val, max_val, std_dev):
        self.assertAlmostEqual(mean_val, stats.mean)
        self.assertAlmostEqual(geo_mean, stats.geom_mean)

        self.assertEqual(min_val, stats.min)
        self.assertEqual(max_val, stats.max)
        self.assertAlmostEqual(std_dev, stats.std_dev)

    def test_123(self):
        stats = StatisticProperties()
        stats.add([1, 2, 3])
        self._assert(stats, 2, 1.817120592, 1, 3, 0.816496580927726)

        stats = StatisticProperties()
        stats.add([1.0, 2.0, 3.0])
        self._assert(stats, 2, 1.817120592, 1.0, 3.0, 0.816496580927726)

    def test_1to49(self):
        stats = StatisticProperties()
        stats.add(self._integers)
        self._assert(stats, 25, 19.112093553, 1, 49, 14.142135623730951)

        stats = StatisticProperties()
        stats.add(self._floats)
        self._assert(stats, 25, 19.112093553, 1.0, 49.0, 14.142135623730951)

    def test_shifted(self):
        stats = StatisticProperties()
        stats.add(self._floats2)
        self._assert(stats, 25 + 2.31, 22.533409416, 1.0 + 2.31, 49.0 + 2.31, 14.142135623730951)

    def test_mixed(self):
        stats = StatisticProperties()
        stats.add(self._mixed)
        self.assertAlmostEqual(27.295918367, stats.mean)
        self._assert(stats, 27.295918367, 22.245044799, 2, 53.5, 14.319929870761944)
