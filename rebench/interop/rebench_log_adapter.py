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


class RebenchLogAdapter(GaugeAdapter):
    """RebenchLogPerformance is the standard log parser of ReBench.
       It reads a simple log format, which includes the number of iterations of
       a benchmark and its runtime in microseconds.

       Note: regular expressions are documented in /docs/extensions.md
    """
    re_log_line = re.compile(
        r"^(?:.*: )?([^\s]+)( [\w\.]+)?: iterations=([0-9]+) "
        + r"runtime: (?P<runtime>(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)"
        + r"(?P<unit>[mu])s")
    re_extra_criterion_log_line = re.compile(
        r"^(?:.*: )?([^\s]+): (?P<criterion>[^:]{1,30}):\s*"
        + r"(?P<value>(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?)"
        + r"(?P<unit>[a-zA-Z]+)")

    re_NPB_partial_invalid = re.compile(r".*Failed.*verification")
    re_NPB_invalid = re.compile(r".*Benchmark done.*verification failed")
    re_incorrect = re.compile(r".*incorrect.*")

    def __init__(self, include_faulty, executor):
        super(RebenchLogAdapter, self).__init__(include_faulty, executor)
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

            measure = None
            match = self.re_log_line.match(line)
            if match:
                time = float(match.group("runtime"))
                if match.group("unit") == "u":
                    time /= 1000
                criterion = (match.group(2) or "total").strip()

                measure = Measurement(invocation, iteration, time, "ms", run_id, criterion)

            else:
                match = self.re_extra_criterion_log_line.match(line)
                if match:
                    value = float(match.group("value"))
                    criterion = match.group("criterion")
                    unit = match.group("unit")

                    measure = Measurement(invocation, iteration, value, unit, run_id, criterion)

            if measure:
                current.add_measurement(measure)

                if measure.is_total():
                    data_points.append(current)
                    current = DataPoint(run_id)
                    iteration += 1

        if not data_points:
            raise OutputNotParseable(data)

        return data_points
