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
import subprocess
from .adapter            import GaugeAdapter, OutputNotParseable
from ..model.data_point  import DataPoint
from ..model.measurement import Measurement


class TimeAdapter(GaugeAdapter):
    """TimePerformance uses the systems time utility to allow measurement of
       unmodified programs or aspects which need to cover the whole program
       execution time.
    """
    re_time = re.compile(r"^(\w+)\s*(\d+)m(\d+\.\d+)s")
    re_time2 = re.compile(r"^(\w+)(\s*)(\d+\.\d+)")

    # To be sure about how to parse the output, give custom format
    # This avoids issues with perhaps none-standard /bin/usr/time
    time_format = '"max rss (kb): %M\nwall-time (secounds): %e\n"'
    re_formatted_time = re.compile(r"^wall-time \(secounds\): (\d+\.\d+)")
    re_formatted_rss  = re.compile(r"^max rss \(kb\): (\d+)")

    def __init__(self, include_faulty):
        GaugeAdapter.__init__(self, include_faulty)
        self._use_formatted_time = False

    def acquire_command(self, command):
        formatted_output = subprocess.call(
            ['/usr/bin/time', '-f', TimeAdapter.time_format, 'sleep', '1'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if formatted_output == 0:
            self._use_formatted_time = True
            return "/usr/bin/time -f %s %s" % (TimeAdapter.time_format, command)
        else:
            # use standard, but without info on memory
            # TODO: add support for reading out memory info on OS X
            return "/usr/bin/time -p %s" % command

    def parse_data(self, data, run_id):
        data_points = []
        current = DataPoint(run_id)

        for line in data.split("\n"):
            if self.check_for_error(line):
                return None

            if self._use_formatted_time:
                m1 = self.re_formatted_rss.match(line)
                m2 = self.re_formatted_time.match(line)
                if m1:
                    mem_kb = float(m1.group(1))
                    measure = Measurement(mem_kb, 'kb', run_id, 'MaxRSS')
                    current.add_measurement(measure)
                elif m2:
                    time = float(m2.group(1)) * 1000
                    measure = Measurement(time, 'ms', run_id, 'total')
                    current.add_measurement(measure)
                    data_points.append(current)
                    current = DataPoint(run_id)
            else:
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

