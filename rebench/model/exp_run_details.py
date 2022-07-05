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
from . import none_or_int, none_or_float, none_or_bool, none_or_dict, \
    remove_important, prefer_important


class ExpRunDetails(object):

    @classmethod
    def compile(cls, config, defaults):
        invocations = prefer_important(config.get('invocations'), defaults.invocations)
        iterations = prefer_important(config.get('iterations'), defaults.iterations)
        warmup = prefer_important(config.get('warmup'), defaults.warmup)

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
        env = none_or_dict(config.get('env', defaults.env))

        return ExpRunDetails(invocations, iterations, warmup, min_iteration_time,
                             max_invocation_time, ignore_timeouts, parallel_interference_factor,
                             execute_exclusively, retries_after_failure, env,
                             defaults.invocations_override, defaults.iterations_override)

    @classmethod
    def empty(cls):
        return ExpRunDetails(None, None, None, None, None, None, None, None, None, None, None, None)

    @classmethod
    def default(cls, invocations_override, iterations_override):
        return ExpRunDetails(1, 1, None, 50, -1, None, None, True, 0, {},
                             invocations_override, iterations_override)

    def __init__(self, invocations, iterations, warmup, min_iteration_time,
                 max_invocation_time, ignore_timeouts, parallel_interference_factor,
                 execute_exclusively, retries_after_failure, env,
                 invocations_override, iterations_override):
        self.invocations = invocations
        self.iterations = iterations
        self.warmup = warmup

        self.min_iteration_time = min_iteration_time
        self.max_invocation_time = max_invocation_time
        self.ignore_timeouts = ignore_timeouts
        self.parallel_interference_factor = parallel_interference_factor
        self.execute_exclusively = execute_exclusively
        self.retries_after_failure = retries_after_failure
        self.env = env

        self.invocations_override = invocations_override
        self.iterations_override = iterations_override

    def resolve_override_and_important(self):
        # resolve overrides
        if self.invocations_override is not None:
            self.invocations = self.invocations_override

        if self.iterations_override is not None:
            self.iterations = self.iterations_override

        # resolve important tags
        self.invocations = remove_important(self.invocations)
        self.iterations = remove_important(self.iterations)
        self.warmup = remove_important(self.warmup)

    def as_dict(self):
        return {
            'warmup': self.warmup,
            'minIterationTime': self.min_iteration_time,
            'maxInvocationTime': self.max_invocation_time
        }
