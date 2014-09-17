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


class GaugeAdapter(object):
    """A GaugeAdapter implements a common interface to evaluate the output of
       benchmarks and to determine measured performance values.
       The GaugeAdapter class also provides some basic helper functionality.
    """

    # definition of some regular expression to identify erroneous runs
    re_error     = re.compile("Error")
    re_segfault  = re.compile("Segmentation fault")
    re_bus_error = re.compile("Bus error")

    def __init__(self, include_faulty):
        self._include_faulty = include_faulty
        self._otherErrorDefinitions = None

    def acquire_command(self, command):
        return command

    def parse_data(self, data, run_id):
        raise NotImplementedError()

    def check_for_error(self, line):
        """Check whether the output line contains one of the common error
           messages. If its an erroneous run, the result has to be discarded.
        """
        if self._include_faulty:
            return False

        if self.re_error.search(line):
            return True
        if self.re_segfault.search(line):
            return True
        if self.re_bus_error.search(line):
            return True

        if self._otherErrorDefinitions:
            for regEx in self._otherErrorDefinitions:
                if regEx.search(line):
                    return True

        return False


class ExecutionDeliveredNoResults(Exception):
    """The exception to be raised when no results were obtained from the given
       data string."""
    def __init__(self, unparsable_data):
        self._unparseable_data = unparsable_data


class OutputNotParseable(ExecutionDeliveredNoResults):
    pass


class ResultsIndicatedAsInvalid(ExecutionDeliveredNoResults):
    pass
