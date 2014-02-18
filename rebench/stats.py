# Copyright (c) 2009-2013 Stefan Marr <http://www.stefan-marr.de/>
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
import operator
import math

## This code is inspired by https://code.google.com/p/python-statlib


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


def geomean(values):
    product = reduce(operator.mul, values, 1)
    return product ** (1.0 / len(values))


def variance(values):
    avg = mean(values)
    var = [(x - avg) ** 2 for x in values]
    return mean(var)


def stddev(values):
    return math.sqrt(variance(values))
