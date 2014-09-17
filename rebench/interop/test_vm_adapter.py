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


class TestVMAdapter(GaugeAdapter):
    """Performance reader for the test case and the definitions
       in test/test.conf
    """

    re_time = re.compile(r"RESULT-(\w+):\s*(\d+\.\d+)")

    def __init__(self, include_faulty):
        super(TestVMAdapter, self).__init__(include_faulty)
        self._otherErrorDefinitions = [re.compile("FAILED")]

    def parse_data(self, data, run_id):
        data_points = []
        current = DataPoint(run_id)

        for line in data.split("\n"):
            if self.check_for_error(line):
                raise ResultsIndicatedAsInvalid(
                    "Output of bench program indicated error.")

            m = TestVMAdapter.re_time.match(line)
            if m:
                measure = Measurement(float(m.group(2)), 'ms', run_id,
                                      m.group(1))
                current.add_measurement(measure)

                if measure.is_total():
                    data_points.append(current)
                    current = DataPoint(run_id)

        if len(data_points) == 0:
            raise OutputNotParseable(data)

        return data_points
