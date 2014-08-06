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


class TimeAdapter(GaugeAdapter):
    """TimePerformance uses the systems time utility to allow measurement of
       unmodified programs or aspects which need to cover the whole program
       execution time.
    """
    re_time = re.compile(r"^(\w+)\s*(\d+)m(\d+\.\d+)s")
    re_time2 = re.compile(r"^(\w+)(\s*)(\d+\.\d+)")

    def acquire_command(self, command):
        return "/usr/bin/time -p %s" % command

    def parse_data(self, data, run_id):
        data_points = []
        current = DataPoint(run_id)

        for line in data.split("\n"):
            if self.check_for_error(line):
                return None

            m1 = self.re_time.match(line)
            m2 = self.re_time2.match(line)
            if m1 or m2:
                m = m1 or m2
                criterion = 'total' if m.group(1) == 'real' else m.group(1)
                time = (float(m.group(2).strip() or 0) * 60 +
                        float(m.group(3))) * 1000
                measure = Measurement(time, 'ms', run_id, criterion)
                current.add_measurement(measure)

                if measure.is_total():
                    data_points.append(current)
                    current = DataPoint(run_id)

        if len(data_points) == 0:
            raise OutputNotParseable(data)

        return data_points


class TimeManualAdapter(TimeAdapter):
    """TimeManualPerformance works like TimePerformance but does expect the
       user to use the /usr/bin/time manually.
       This is useful for runs on remote machines like the Tilera or ARM boards.
    """
    def acquire_command(self, command):
        return command

