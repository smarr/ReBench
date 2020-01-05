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


class TerminationCheck(object):
    def __init__(self, run_id, ui):
        self._run_id = run_id
        self._ui = ui
        self._consecutive_erroneous_executions = 0
        self._failed_execution_count = 0
        self._fail_immediately = False

    def fail_immediately(self):
        self._fail_immediately = True

    def indicate_failed_execution(self):
        self._consecutive_erroneous_executions += 1
        self._failed_execution_count += 1

    def indicate_successful_execution(self):
        self._consecutive_erroneous_executions = 0

    def fails_consecutively(self):
        return (self._fail_immediately or
                (self._consecutive_erroneous_executions > 0 and
                 self._consecutive_erroneous_executions >= self._run_id.retries_after_failure))

    def has_too_many_failures(self, number_of_data_points):
        return (self._fail_immediately or
                (self._failed_execution_count > 6) or (
                    number_of_data_points > 10 and (
                        self._failed_execution_count > number_of_data_points / 2)))

    def should_terminate(self, number_of_data_points, cmd):
        if self._fail_immediately:
            self._ui.warning("{ind}Marked to fail immediately.\n", self._run_id, cmd)
        if self.fails_consecutively():
            msg = "{ind}Execution has failed, benchmark is aborted.\n"
            if self._consecutive_erroneous_executions > 0:
                msg += "{ind}{ind}The benchmark failed "
                msg += str(self._consecutive_erroneous_executions) + " times in a row.\n"
            self._ui.warning(msg, self._run_id, cmd)
            return True
        elif self.has_too_many_failures(number_of_data_points):
            self._ui.warning(
                "{ind}Many runs are failing, benchmark is aborted.\n", self._run_id, cmd)
            return True
        elif self._run_id.completed_invocations >= self._run_id.invocations:
            return True
        else:
            return False
