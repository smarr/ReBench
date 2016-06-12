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


## This code is inspired by https://code.google.com/p/python-statlib

import unittest
from .. import statistics as stats

are_numpy_and_scipy_available = False
try:
    import numpy
    import scipy.stats
    # import scipy.stats.distributions -- not yet implemented
    are_numpy_and_scipy_available = True
except ImportError:
    are_numpy_and_scipy_available = False


class StatsTest(unittest.TestCase):
    
    def setUp(self):
        self._integers = range(1, 50)
        self._floats   = [float(x)        for x in self._integers]
        self._floats2  = [float(x) + 2.31 for x in self._integers]
        
        self._mixed    = [x if x % 2 == 0 else float(x) + 4.5
                                          for x in self._integers]
    
    
    def test_mean_simple(self):
        self.assertEqual(2, stats.mean([1, 2, 3]))
        self.assertAlmostEqual(2, stats.mean([1.0, 2.0, 3.0]))
        
        self.assertAlmostEqual(25,           stats.mean(self._integers))
        self.assertAlmostEqual(25,           stats.mean(self._floats))
        self.assertAlmostEqual(25 + 2.31,    stats.mean(self._floats2))
        self.assertAlmostEqual(27.295918367, stats.mean(self._mixed))
    
    @unittest.skipUnless(are_numpy_and_scipy_available,
                         "NumPy or SciPy is not available")
    def test_mean_vs_numpy(self):
        self.assertEqual(numpy.mean([1, 2, 3]),
                         stats.mean([1, 2, 3]))
        self.assertAlmostEqual(numpy.mean([1.0, 2.0, 3.0]),
                               stats.mean([1.0, 2.0, 3.0]))
        
        self.assertAlmostEqual(numpy.mean(self._integers),
                               stats.mean(self._integers))
        
        self.assertAlmostEqual(numpy.mean(self._floats),
                               stats.mean(self._floats))
        
        self.assertAlmostEqual(numpy.mean(self._floats2),
                               stats.mean(self._floats2))
        
        self.assertAlmostEqual(numpy.mean(self._mixed),
                               stats.mean(self._mixed))
    
    def test_median_simple(self):
        self.assertEqual(      2.5, stats.median([  1,   2,   3,   4]))
        self.assertAlmostEqual(2.5, stats.median([1.0, 2.0, 3.0, 4.0]))
        
        self.assertAlmostEqual(25, stats.median(self._integers))
        self.assertAlmostEqual(25, stats.median(self._floats))
        self.assertAlmostEqual(25 + 2.31, stats.median(self._floats2))
        self.assertAlmostEqual(27.5, stats.median(self._mixed))
    
    @unittest.skipUnless(are_numpy_and_scipy_available,
                         "NumPy or SciPy is not available")
    def test_median_vs_numpy(self):
        self.assertEqual(numpy.median([1, 2, 3, 4]),
                         stats.median([1, 2, 3, 4]))
        self.assertAlmostEqual(numpy.median([1.0, 2.0, 3.0, 4.0]),
                               stats.median([1.0, 2.0, 3.0, 4.0]))
        
        self.assertAlmostEqual(numpy.median(self._integers),
                               stats.median(self._integers))
        
        self.assertAlmostEqual(numpy.median(self._floats),
                               stats.median(self._floats))
        
        self.assertAlmostEqual(numpy.median(self._floats2),
                               stats.median(self._floats2))
        
        self.assertAlmostEqual(numpy.median(self._mixed),
                               stats.median(self._mixed))
    
    def test_geomean_simple(self):
        self.assertAlmostEqual( 1.817120592, stats.geo_mean([  1,   2,   3]))
        self.assertAlmostEqual( 1.817120592, stats.geo_mean([1.0, 2.0, 3.0]))
        
        self.assertAlmostEqual(19.112093553, stats.geo_mean(self._integers))
        self.assertAlmostEqual(19.112093553, stats.geo_mean(self._floats))
        self.assertAlmostEqual(22.533409416, stats.geo_mean(self._floats2))
        self.assertAlmostEqual(22.245044799, stats.geo_mean(self._mixed))
    
    @unittest.skipUnless(are_numpy_and_scipy_available,
                         "NumPy or SciPy is not available")
    def test_geomean_vs_scipy(self):
        self.assertAlmostEqual(scipy.stats.gmean([1, 2, 3]),
                                   stats.geo_mean([1, 2, 3]))
        self.assertAlmostEqual(scipy.stats.gmean([1.0, 2.0, 3.0]),
                                   stats.geo_mean([1.0, 2.0, 3.0]))
        
        self.assertAlmostEqual(scipy.stats.gmean(self._integers),
                                   stats.geo_mean(self._integers))
        
        self.assertAlmostEqual(scipy.stats.gmean(self._floats),
                                   stats.geo_mean(self._floats))
        
        self.assertAlmostEqual(scipy.stats.gmean(self._floats2),
                                   stats.geo_mean(self._floats2))
        
        self.assertAlmostEqual(scipy.stats.gmean(self._mixed),
                                   stats.geo_mean(self._mixed))
    
    def test_stddev_simple(self):
        self.assertAlmostEqual(0.8164965809,
                               stats.stddev([1, 2, 3]))
        self.assertAlmostEqual(0.8164965809,
                               stats.stddev([1.0, 2.0, 3.0]))
        
        self.assertAlmostEqual(14.142135623,
                               stats.stddev(self._integers))
        
        self.assertAlmostEqual(14.142135623,
                               stats.stddev(self._floats))
        
        self.assertAlmostEqual(14.142135623,
                               stats.stddev(self._floats2))
        
        self.assertAlmostEqual(14.319929870,
                               stats.stddev(self._mixed))
    
    @unittest.skipUnless(are_numpy_and_scipy_available,
                         "NumPy or SciPy is not available")
    def test_stddev_vs_numpy(self):
        self.assertAlmostEqual(numpy.std(   [1, 2, 3]),
                               stats.stddev([1, 2, 3]))
        self.assertAlmostEqual(numpy.std(   [1.0, 2.0, 3.0]),
                               stats.stddev([1.0, 2.0, 3.0]))
        
        self.assertAlmostEqual(numpy.std(   self._integers),
                               stats.stddev(self._integers))
        
        self.assertAlmostEqual(numpy.std(   self._floats),
                               stats.stddev(self._floats))
        
        self.assertAlmostEqual(numpy.std(   self._floats2),
                               stats.stddev(self._floats2))
        
        self.assertAlmostEqual(numpy.std(   self._mixed),
                               stats.stddev(self._mixed))

# Not Yet Implemented
#    @unittest.skipUnless(are_numpy_and_scipy_available, "NumPy or SciPy is not available")
#    def test_norm_distribution(self):
#        self.fail("not yet implemented")
#    
#    @unittest.skipUnless(are_numpy_and_scipy_available, "NumPy or SciPy is not available")
#    def test_t_distribution(self):
#        self.fail("not yet implemented")

