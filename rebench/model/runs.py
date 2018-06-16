# Copyright (c) 2009-2018 Stefan Marr <http://www.stefan-marr.de/>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
import logging


class TerminationCheck(object):
    def __init__(self, benchmark):
        self._benchmark = benchmark
        self._num_invocations = 0
        self._consecutive_erroneous_executions = 0
        self._failed_execution_count = 0
        self._fail_immediately = False

    def fail_immediately(self):
        self._fail_immediately = True

    def indicate_invocation_start(self):
        self._num_invocations += 1

    def indicate_failed_execution(self):
        self._consecutive_erroneous_executions += 1
        self._failed_execution_count += 1

    def indicate_successful_execution(self):
        self._consecutive_erroneous_executions = 0

    def fails_consecutively(self):
        return (self._fail_immediately or
                self._consecutive_erroneous_executions >= 3)

    def has_too_many_failures(self, number_of_data_points):
        return (self._fail_immediately or
                (self._failed_execution_count > 6) or (
                    number_of_data_points > 10 and (
                        self._failed_execution_count > number_of_data_points / 2)))

    def should_terminate(self, number_of_data_points):
        if self._fail_immediately:
            logging.info(
                "%s was marked to fail immediately" % self._benchmark.name)
        if self.fails_consecutively():
            logging.error(("Three executions of %s have failed in a row, " +
                           "benchmark is aborted") % self._benchmark.name)
            return True
        elif self.has_too_many_failures(number_of_data_points):
            logging.error("Many runs of %s are failing, benchmark is aborted."
                          % self._benchmark.name)
            return True
        elif self._num_invocations >= self._benchmark.run_details.invocations:
            return True
        else:
            return False
