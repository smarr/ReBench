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
from ..ui import UIError


class DataPoint(object):
    def __init__(self, run_id):
        self._run_id = run_id
        self._measurements = []
        self._total = None
        self._invocation = -1

    @property
    def run_id(self):
        return self._run_id

    @property
    def invocation(self):
        return self._invocation

    def number_of_measurements(self):
        return len(self._measurements)

    def add_measurement(self, measurement):
        if self._invocation == -1:
            self._invocation = measurement.invocation
        elif self._invocation != measurement.invocation:
            raise UIError("A data point is expected to represent a single invocation " +
                          "but we got invocation " + str(measurement.invocation) +
                          " and " + str(self._invocation) + "\n", None)

        self._measurements.append(measurement)
        if measurement.is_total():
            if self._total is not None:
                raise ValueError("A data point should only include one " +
                                 "'total' measurement.")
            self._total = measurement

    def _get_measurements_reordered(self):
        # re-order so that total is last.
        out = [m for m in self._measurements if not m.is_total()]
        def _find_total(measurements):
            for measurement in measurements:
                if measurement.is_total():
                    return measurement # Highlander
            return None
        total = _find_total(self._measurements)
        if total is not None:
            out.append(total)
        return out

    def get_measurements(self):
        if self._measurements and not self._measurements[-1].is_total():
            return self._get_measurements_reordered()
        return self._measurements

    def get_total_value(self):
        return self._total.value if self._total else None

    def get_total_unit(self):
        return self._total.unit
