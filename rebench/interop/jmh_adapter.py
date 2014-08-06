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


class JMHAdapter(GaugeAdapter):
    """
    An adapter for parsing logs produced by JMH, a Java benchmarking harness.
    """
    re_result_line = re.compile(r"^Iteration\s+(\d+):\s+(\d+(?:\.\d+)?)\s+(.+)")
    re_bench = re.compile(r"^# Benchmark: (.+)")

    def parse_data(self, data, run_id):
        data_points = []

        for line in data.split("\n"):
            if self.check_for_error(line):
                raise ResultsIndicatedAsInvalid(
                    "Output of bench program indicated error.")

            ## TODO: make sure that we support JMH in a way that we get the results
            ## for the correct benchmarks...

            # # first, make sure we parse for a one benchmark, otherwise skip
            # # through all the lines
            # if self.re_bench.match(line):
            #     current = DataPoint(run_id)
            #     continue
            # if current is None:
            #     continue

            # now we are sure that we parse for a benchmark and can collect data
            m = self.re_result_line.match(line)
            if m:
                value = float(m.group(2))
                unit  = m.group(3)
                criterion = "total"

                dp = DataPoint(run_id)
                dp.add_measurement(Measurement(value, unit, run_id, criterion))
                data_points.append(dp)

        if len(data_points) == 0:
            raise OutputNotParseable(data)
        return data_points
