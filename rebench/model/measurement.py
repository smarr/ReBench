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
from datetime import datetime

from .run_id import RunId


class Measurement(object):
    def __init__(self, value, unit, run_id, criterion = 'total',
                 timestamp = None):
        self._run_id    = run_id
        self._criterion = criterion
        self._value     = value
        self._unit      = unit
        self._timestamp = timestamp or datetime.now()
        
    def is_total(self):
        return self._criterion == 'total'
    
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
    def timestamp(self):
        return self._timestamp

    @property
    def run_id(self):
        return self._run_id

    TIME_FORMAT = "%Y-%m-%dT%H:%M:%S"

    def as_str_list(self):
        return ["[" + self._timestamp.strftime(self.TIME_FORMAT) + "]",
                "%f" % self._value,
                self._unit,
                self._criterion] + self._run_id.as_str_list()

    @classmethod
    def from_str_list(cls, data_store, str_list):

        timestamp = datetime.strptime(str_list[0][1:-1], cls.TIME_FORMAT)
        value     = float(str_list[1])
        unit      = str_list[2]
        criterion = str_list[3]
        run_id    = RunId.from_str_list(data_store, str_list[4:])

        return Measurement(value, unit, run_id, criterion, timestamp)
