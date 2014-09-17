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


class MultivariateAdapter(GaugeAdapter):
    """Performance reader for multiple datapoints with multiple variables

    In its simplest form compatible to TestVMPerformance.
    """

    variable_re = re.compile(r"(?:(\d+):)?RESULT-(\w+):(?:(\w+):)?\s*(\d+(\.\d+)?)")
    # optional datapoint counter, mandantory variable, optional unit, mandantory int-or-float

    def __init__(self, include_faulty):
        super(MultivariateAdapter, self).__init__(include_faulty)
        self._otherErrorDefinitions = [re.compile("FAILED")]

    def parse_data(self, data, run_id):
        data_points = []
        current = DataPoint(run_id)

        for line in data.split("\n"):
            if self.check_for_error(line):
                raise ResultsIndicatedAsInvalid(
                    "Output of bench program indicated error.")

            m = self.variable_re.match(line)
            if m:
                (c, variable, unit, value_thing, floatpart) = m.groups()

                # check for possible data point carry over
                if c is not None:
                    counter = int(c)
                    while counter >= len(data_points):
                        data_points.append(DataPoint(run_id))
                    current = data_points[counter]

                # determine value type
                if floatpart is None:
                    value = int(value_thing)
                else:
                    value = float(value_thing)

                measure = Measurement(value, unit if unit is not None else 'ms',
                                      run_id, variable)
                current.add_measurement(measure)

                if c is None and measure.is_total():
                    # compatibility for TestVMPerformance
                    data_points.append(current)
                    current = DataPoint(run_id)


        if len(data_points) == 0:
            raise OutputNotParseable(data)

        return data_points
