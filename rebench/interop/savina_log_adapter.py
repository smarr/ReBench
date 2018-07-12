# Copyright (c) 2009-2015 Stefan Marr <http://www.stefan-marr.de/>
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

from .adapter import GaugeAdapter, OutputNotParseable

from ..model.data_point  import DataPoint
from ..model.measurement import Measurement


class SavinaLogAdapter(GaugeAdapter):
    """ SavinaLogAdapter parses the output of the Savina benchmark harness. """
    re_log_line = re.compile(
        r"^([\w\.]+)\s+Iteration-(?:\d+):\s+([0-9]+\.[0-9]+) ms")

    def parse_data(self, data, run_id, invocation):
        iteration = 1
        data_points = []

        for line in data.split("\n"):
            match = self.re_log_line.match(line)
            if match:
                time = float(match.group(2))
                measure = Measurement(invocation, iteration, time, 'ms', run_id, 'total')
                current = DataPoint(run_id)
                current.add_measurement(measure)
                data_points.append(current)
                iteration += 1

        if not data_points:
            raise OutputNotParseable(data)

        return data_points
