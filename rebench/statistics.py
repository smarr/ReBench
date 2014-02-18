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
import math
import logging

try:
    import numpy
    import scipy.stats
    import scipy.stats.distributions as dist
    
    # provide a common interface for the relevant functions
    import imp
    stats = imp.new_module("stats")
    stats.mean     = numpy.mean
    stats.median   = numpy.median
    stats.geomean  = scipy.stats.gmean
    stats.stddev   = numpy.std
    stats.norm_ppf = dist.norm.ppf
    stats.t_ppf    = dist.t.ppf
except ImportError:
    logging.error("Loading scipy.stats failed. " +
                  "A replacement is not yet completely implemented.")
    import stats


class StatisticProperties:
    """
    The statistics class calculates the statistic
    properties of a given set of data samples, i.e., the chosen values
    from a set of data points
    """
    
    def __init__(self, data_samples, confidence_level):
        self._data_samples     = data_samples
        self._confidence_level = confidence_level

        self.mean                   = 0
        self.geom_mean              = 0
        self.median                 = 0
        self.std_dev                = 0
        self.num_samples            = 0
        self.min                    = 0
        self.max                    = 0
        self.conf_interval_low      = 0
        self.conf_interval_high     = 0
        self.conf_interval_size_abs = 0
        self.conf_interval_size     = 0

        if self._data_samples:
            self.num_samples = len(self._data_samples)
            self._calc_basic_statistics()
            self._calc_confidence(confidence_level)
        else:
            self.num_samples = 0

    def _calc_basic_statistics(self):
        """This function determines the mean and the standard deviation
           of the data sample.
           Furthermore, several other simple properties are determined.
        """
        self.mean        = stats.mean(self._data_samples)
        self.geom_mean   = stats.geomean(self._data_samples)
        self.median      = stats.median(self._data_samples)
        self.std_dev     = stats.stddev(self._data_samples)

        self.min = min(self._data_samples)
        self.max = max(self._data_samples)
        
    def as_tuple(self):
        return (self.mean,
                self.geom_mean,
                self.median,
                self.std_dev,
                self.num_samples,
                self.min,
                self.max,
                self.conf_interval_low,
                self.conf_interval_high,
                self.conf_interval_size_abs,
                self.conf_interval_size)
    
    @classmethod
    def tuple_mapping(cls):
        return ('arithmetic mean', 'geometric mean', 'median', 'stdDev',
                '#samples', 'min', 'max', 'Conf. Interval Low',
                'Conf. Interval High', 'Conf. Interval Size Abs.',
                'Conf.IntervalSize/Mean')

    def _calc_confidence(self, confidence_level):
        """
        Depending on the number of samples, different distributions
        are more optimal.
        
        Uses normal distribution, for >30 values
        javastats used students,
        i.e., t distribution for fewer values (<=30 values)
        """
        if self.num_samples > 30:
            distribution = stats.norm_ppf((1 + confidence_level) / 2.0)
        else:
            df   = self.num_samples - 1
            distribution = stats.t_ppf((1 + confidence_level) / 2.0, df)
            
        self._confidence_for_samples(distribution)
            
    def _confidence_for_samples(self, distribution):
        """This function determines the confidence interval for a given 
           set of samples, as well as  and the size of the confidence 
           interval and its percentage of the mean.
        """
        self.conf_interval_low  = self.mean - (distribution * self.std_dev / math.sqrt(self.num_samples))
        self.conf_interval_high = self.mean + (distribution * self.std_dev / math.sqrt(self.num_samples))
        
        self.conf_interval_size_abs = (self.conf_interval_high
                                       - self.conf_interval_low)
        self.conf_interval_size     = self.conf_interval_size_abs / self.mean
