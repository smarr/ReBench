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
from .run_id import RunId


class Measurement(object):
    def __init__(self, invocation, iteration, value, unit,
                 run_id, criterion='total', line_number=None, filename=None):
        self._invocation = invocation
        self._iteration = iteration
        self._value = value
        self._unit = unit
        self._run_id = run_id
        self._criterion = criterion
        assert unit is not None
        self._line_number = line_number
        self._filename = filename

    def is_total(self):
        return self._criterion == 'total'

    @property
    def invocation(self):
        return self._invocation

    @property
    def iteration(self):
        return self._iteration

    @property
    def criterion(self):
        return self._criterion

    @property
    def value(self):
        return self._value

    @property
    def unit(self):
        return self._unit

    @property
    def run_id(self):
        return self._run_id

    @property
    def filename(self):
        return self._filename

    @property
    def line_number(self):
        return self._line_number

    def as_str_list(self):
        if isinstance(self._value, float):
            val = "%f" % self.value
        else:
            val = "%s" % self.value

        return [str(self._invocation), str(self._iteration),
                val,
                self._unit,
                self._criterion] + self._run_id.as_str_list()

    @classmethod
    def from_str_list(cls, data_store, str_list, line_number=None, filename=None):
        invocation = int(str_list[0])
        iteration = int(str_list[1])
        value = float(str_list[2])
        unit = str_list[3]
        criterion = str_list[4]
        run_id = RunId.from_str_list(data_store, str_list[5:])

        return Measurement(invocation, iteration, value, unit, run_id,
                           criterion, line_number, filename)

    def as_dict(self):
        result = dict()
        result['c'] = self._criterion
        result['in'] = self._invocation
        result['it'] = self._iteration
        result['u'] = self._unit
        result['v'] = self._value
        return result
