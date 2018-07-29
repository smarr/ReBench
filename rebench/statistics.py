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


class StatisticProperties(object):
    """
    The class maintains running statistics for the added data points.
    Data points can be added one by one, or as lists of values.
    """

    def __init__(self):
        self.num_samples = 0

        self.mean = 0.0
        self.geom_mean = 0.0
        self.std_dev = 0.0
        self.min = 0
        self.max = 0

        # used to calculate std_dev
        # Variance (sigma^2) * num_samples
        self._variance_times_num_samples = 0
        # used to calculate geomean
        self._product_of_samples = 1.0

    def add(self, samples):
        for sample in samples:
            self.add_sample(sample)

    def add_sample(self, sample):
        if self.num_samples == 0:
            self.mean = float(sample)
            self.geom_mean = float(sample)
            self._product_of_samples = float(sample)

            self.min = sample
            self.max = sample
            self.num_samples = 1
        else:
            self.num_samples += 1
            prev_mean = self.mean
            self.mean = prev_mean + ((sample - prev_mean) / self.num_samples)

            self._product_of_samples = self._product_of_samples * float(sample)
            self.geom_mean = self._product_of_samples ** (1/float(self.num_samples))

            self._variance_times_num_samples = (self._variance_times_num_samples +
                                                ((sample - prev_mean) * (sample - self.mean)))
            self.std_dev = math.sqrt(self._variance_times_num_samples / self.num_samples)

            if self.min > sample:
                self.min = sample

            if self.max < sample:
                self.max = sample

    def as_tuple(self):
        return (self.mean,
                self.geom_mean,
                self.std_dev,
                self.num_samples,
                self.min,
                self.max)

    @classmethod
    def tuple_mapping(cls):
        return ('arithmetic mean', 'geometric mean', 'stdDev',
                '#samples', 'min', 'max')
