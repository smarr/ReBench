# Copyright (c) 2018 Stefan Marr <http://www.stefan-marr.de/>
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
from . import none_or_int, none_or_float, none_or_bool


class ExpRunDetails(object):

    @classmethod
    def compile(cls, config, defaults):
        invocations = none_or_int(config.get('invocations', defaults.invocations))
        iterations = none_or_int(config.get('iterations', defaults.iterations))
        warmup = none_or_int(config.get('warmup', defaults.warmup))

        min_iteration_time = none_or_int(config.get('min_iteration_time',
                                                    defaults.min_iteration_time))
        max_invocation_time = none_or_int(config.get('max_invocation_time',
                                                     defaults.max_invocation_time))
        ignore_timeouts = none_or_bool(config.get('ignore_timeouts',
                                                  defaults.ignore_timeouts))

        parallel_interference_factor = none_or_float(config.get(
            'parallel_interference_factor', defaults.parallel_interference_factor))
        execute_exclusively = none_or_bool(config.get('execute_exclusively',
                                                      defaults.execute_exclusively))

        retries_after_failure = none_or_int(config.get('retries_after_failure',
                                                       defaults.retries_after_failure))

        return ExpRunDetails(invocations, iterations, warmup, min_iteration_time,
                             max_invocation_time, ignore_timeouts, parallel_interference_factor,
                             execute_exclusively, retries_after_failure,
                             defaults.invocations_override, defaults.iterations_override)

    @classmethod
    def empty(cls):
        return ExpRunDetails(None, None, None, None, None, None, None, None, None, None, None)

    @classmethod
    def default(cls, invocations_override, iterations_override):
        return ExpRunDetails(1, 1, None, 50, -1, None, None, True, 0,
                             invocations_override, iterations_override)

    def __init__(self, invocations, iterations, warmup, min_iteration_time,
                 max_invocation_time, ignore_timeouts, parallel_interference_factor,
                 execute_exclusively, retries_after_failure,
                 invocations_override, iterations_override):
        self._invocations = invocations
        self._iterations = iterations
        self._warmup = warmup

        self._min_iteration_time = min_iteration_time
        self._max_invocation_time = max_invocation_time
        self._ignore_timeouts = ignore_timeouts
        self._parallel_interference_factor = parallel_interference_factor
        self._execute_exclusively = execute_exclusively
        self._retries_after_failure = retries_after_failure

        self._invocations_override = invocations_override
        self._iterations_override = iterations_override

    @property
    def invocations(self):
        return self._invocations

    @property
    def iterations(self):
        return self._iterations

    @property
    def invocations_override(self):
        return self._invocations_override

    @property
    def iterations_override(self):
        return self._iterations_override

    @property
    def warmup(self):
        return self._warmup

    @property
    def min_iteration_time(self):
        return self._min_iteration_time

    @property
    def max_invocation_time(self):
        return self._max_invocation_time

    @property
    def ignore_timeouts(self):
        return self._ignore_timeouts

    @property
    def parallel_interference_factor(self):
        return self._parallel_interference_factor

    @property
    def execute_exclusively(self):
        return self._execute_exclusively

    @property
    def retries_after_failure(self):
        return self._retries_after_failure

    def as_dict(self):
        result = dict()
        result['warmup'] = self._warmup
        result['minIterationTime'] = self._min_iteration_time
        result['maxInvocationTime'] = self._max_invocation_time
        return result
