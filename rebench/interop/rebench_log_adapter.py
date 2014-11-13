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
    """
    re_log_line = re.compile(
        r"^(?:.*: )?([\w\.]+)( [\w\.]+)?: iterations=([0-9]+) runtime: ([0-9]+)([mu])s")

    re_NPB_partial_invalid = re.compile(r".*Failed.*verification")
    re_NPB_invalid = re.compile(r".*Benchmark done.*verification failed")
    re_incorrect   = re.compile(r".*incorrect.*")

    def __init__(self, include_faulty):
        super(RebenchLogAdapter, self).__init__(include_faulty)
        self._otherErrorDefinitions = [self.re_NPB_partial_invalid,
                                       self.re_NPB_invalid, self.re_incorrect]

    def parse_data(self, data, run_id):
        data_points = []
        current = DataPoint(run_id)

        for line in data.split("\n"):
            if self.check_for_error(line):
                raise ResultsIndicatedAsInvalid(
                    "Output of bench program indicated error.")

            m = self.re_log_line.match(line)
            if m:
                time = float(m.group(4))
                if m.group(5) == "u":
                    time /= 1000
                criterion = (m.group(2) or 'total').strip()

                measure = Measurement(time, 'ms', run_id, criterion)
                current.add_measurement(measure)

                if measure.is_total():
                    data_points.append(current)
                    current = DataPoint(run_id)

        if len(data_points) == 0:
            raise OutputNotParseable(data)

        return data_points
