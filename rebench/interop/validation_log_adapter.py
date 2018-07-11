# Copyright (c) 2009-2014 Stefan Marr <http://www.stefan-marr.de/>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
import re

from .adapter         import GaugeAdapter, OutputNotParseable,\
    ResultsIndicatedAsInvalid

from ..model.data_point  import DataPoint
from ..model.measurement import Measurement


class ValidationLogAdapter(GaugeAdapter):
    """ValidationLogPerformance is the log parser for SOMns ImpactHarness.
       It reads a simple log format, which includes the number of iterations of
       a benchmark, its runtime in microseconds and if it was successful.
    """
    re_log_line = re.compile(
        r"^(?:.*: )?([\w\.]+)( [\w\.]+)?: iterations=([0-9]+)"
        r" runtime: ([0-9]+)([mu])s success: (true|false)")

    re_actors = re.compile(
        r"^\[Total\]\s+A#([0-9]+)\s+M#([0-9]+)\s+P#([0-9]+)")

    re_NPB_partial_invalid = re.compile(r".*Failed.*verification")
    re_NPB_invalid = re.compile(r".*Benchmark done.*verification failed")
    re_incorrect = re.compile(r".*incorrect.*")

    def __init__(self, include_faulty):
        super(ValidationLogAdapter, self).__init__(include_faulty)
        self._other_error_definitions = [self.re_NPB_partial_invalid,
                                         self.re_NPB_invalid, self.re_incorrect]

    def parse_data(self, data, run_id, invocation):
        iteration = 1
        data_points = []
        current = DataPoint(run_id)

        for line in data.split("\n"):
            if self.check_for_error(line):
                raise ResultsIndicatedAsInvalid(
                    "Output of bench program indicated error.")

            match = self.re_log_line.match(line)
            if match:
                time = float(match.group(4))
                if match.group(5) == "u":
                    time /= 1000
                criterion = (match.group(2) or 'total').strip()
                success_measure = Measurement(invocation, iteration,
                                              match.group(6) == "true", 'bool', run_id, 'Success')
                measure = Measurement(invocation, iteration, time, 'ms', run_id, criterion)
                current.add_measurement(success_measure)
                current.add_measurement(measure)

                if measure.is_total():
                    data_points.append(current)
                    current = DataPoint(run_id)
                    iteration += 1
            else:
                match = self.re_actors.match(line)
                if match:
                    measure1 = Measurement(invocation, iteration,
                                           int(match.group(1)), 'count', run_id, 'Actors')
                    measure2 = Measurement(invocation, iteration,
                                           int(match.group(2)), 'count', run_id, 'Messages')
                    measure3 = Measurement(invocation, iteration,
                                           int(match.group(3)), 'count', run_id, 'Promises')
                    measure4 = Measurement(invocation, iteration,
                                           0, 'ms', run_id, 'total')
                    current.add_measurement(measure1)
                    current.add_measurement(measure2)
                    current.add_measurement(measure3)
                    current.add_measurement(measure4)
                    data_points.append(current)
                    current = DataPoint(run_id)
                    iteration += 1

        if not data_points:
            raise OutputNotParseable(data)

        return data_points
