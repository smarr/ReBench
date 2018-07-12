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
    re_formatted_rss = re.compile(r"^max rss \(kb\): (\d+)")

    def __init__(self, include_faulty):
        GaugeAdapter.__init__(self, include_faulty)
        self._use_formatted_time = False

    def acquire_command(self, command):
        try:
            formatted_output = subprocess.call(
                ['/usr/bin/time', '-f', TimeAdapter.time_format, '/bin/sleep', '1'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError:
            formatted_output = 1
        if formatted_output == 0:
            self._use_formatted_time = True
            return "/usr/bin/time -f %s %s" % (TimeAdapter.time_format, command)
        else:
            # use standard, but without info on memory
            # TODO: add support for reading out memory info on OS X
            return "/usr/bin/time -p %s" % command

    def parse_data(self, data, run_id, invocation):
        iteration = 1
        data_points = []
        current = DataPoint(run_id)
        total_measure = None

        for line in data.split("\n"):
            if self.check_for_error(line):
                return None

            if self._use_formatted_time:
                match1 = self.re_formatted_rss.match(line)
                match2 = self.re_formatted_time.match(line)
                if match1:
                    mem_kb = float(match1.group(1))
                    measure = Measurement(invocation, iteration, mem_kb, 'kb', run_id, 'MaxRSS')
                    current.add_measurement(measure)
                elif match2:
                    time = float(match2.group(1)) * 1000
                    measure = Measurement(invocation, iteration, time, 'ms', run_id, 'total')
                    current.add_measurement(measure)
                    data_points.append(current)
                    current = DataPoint(run_id)
                    iteration += 1
            else:
                match1 = self.re_time.match(line)
                match2 = self.re_time2.match(line)
                if match1 or match2:
                    match = match1 or match2
                    criterion = 'total' if match.group(1) == 'real' else match.group(1)
                    time = (float(match.group(2).strip() or 0) * 60 +
                            float(match.group(3))) * 1000
                    measure = Measurement(invocation, iteration, time, 'ms', run_id, criterion)
                    if measure.is_total():
                        total_measure = measure
                    else:
                        current.add_measurement(measure)
                else:
                    measure = None

                if current.number_of_measurements() == 3 and \
                        current.get_total_value() is not None:
                    data_points.append(current)
                    current = DataPoint(run_id)
                    iteration += 1

        if total_measure:
            current.add_measurement(total_measure)
            data_points.append(current)

        if not data_points:
            raise OutputNotParseable(data)

        return data_points


class TimeManualAdapter(TimeAdapter):
    """TimeManualPerformance works like TimePerformance but does expect the
       user to use the /usr/bin/time manually.
       This is useful for runs on remote machines like the Tilera or ARM boards.
    """
    def acquire_command(self, command):
        return command
