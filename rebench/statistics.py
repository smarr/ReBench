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
import copy
import math
import operator


def mean(values):
    return sum(values) / float(len(values))


def median(values):
    values_ = copy.deepcopy(values)
    values_.sort()

    if len(values_) % 2 == 0:
        index = len(values_) / 2
        return float(values_[index] + values_[index - 1]) / 2
    else:
        index = len(values_) / 2
        return values_[index]


def geo_mean(values):
    product = reduce(operator.mul, values, 1)
    return product ** (1.0 / len(values))


def variance(values):
    avg = mean(values)
    var = [(x - avg) ** 2 for x in values]
    return mean(var)


def stddev(values):
    return math.sqrt(variance(values))


class StatisticProperties:
    """
    The statistics class calculates the statistic
    properties of a given set of data samples, i.e., the chosen values
    from a set of data points
    """
    
    def __init__(self, data_samples):
        self._data_samples     = data_samples

        self.mean                   = 0
        self.geom_mean              = 0
        self.median                 = 0
        self.std_dev                = 0
        self.num_samples            = 0
        self.min                    = 0
        self.max                    = 0

        if self._data_samples:
            self.num_samples = len(self._data_samples)
            self._calc_basic_statistics()
        else:
            self.num_samples = 0

    def _calc_basic_statistics(self):
        """This function determines the mean and the standard deviation
           of the data sample.
           Furthermore, several other simple properties are determined.
        """
        self.mean        = mean(self._data_samples)
        self.geom_mean   = geo_mean(self._data_samples)
        self.median      = median(self._data_samples)
        self.std_dev     = stddev(self._data_samples)

        self.min = min(self._data_samples)
        self.max = max(self._data_samples)
        
    def as_tuple(self):
        return (self.mean,
                self.geom_mean,
                self.median,
                self.std_dev,
                self.num_samples,
                self.min,
                self.max)
    
    @classmethod
    def tuple_mapping(cls):
        return ('arithmetic mean', 'geometric mean', 'median', 'stdDev',
                '#samples', 'min', 'max')
