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
from typing import Optional, Mapping, Any
from . import none_or_int, none_or_float, none_or_bool, none_or_dict, \
    remove_important, prefer_important
from .denoise import Denoise

def _lt_of_env_dict(a: dict, b: dict):
    assert a != b

    if len(a) != len(b):
        return len(a) < len(b)

    for k in sorted(a.keys()):
        if k not in b:
            return True

        if a[k] != b[k]:
            return a[k] < b[k]

    # This case should never be reached, because we already checked for equality
    assert False, "Unexpected case reached in _lt_of_env_dict"

class ExpRunDetails(object):

    @classmethod
    def compile(cls, config, defaults) -> "ExpRunDetails":
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

        denoise = Denoise.compile(config.get('denoise', {}), defaults.denoise)

        return ExpRunDetails(invocations, iterations, warmup, min_iteration_time,
                             max_invocation_time, ignore_timeouts, parallel_interference_factor,
                             execute_exclusively, retries_after_failure, env, denoise,
                             defaults.invocations_override, defaults.iterations_override)

    @classmethod
    def empty(cls):
        return ExpRunDetails(None, None, None, None, None, None, None, None, None,
                             None, None, None, None)

    @classmethod
    def default(cls, invocations_override, iterations_override):
        return ExpRunDetails(1, 1, None, 50, -1, None, None, True, 0, {}, Denoise.default(),
                             invocations_override, iterations_override)

    def __init__(self, invocations: Optional[int], iterations: Optional[int], warmup: Optional[int],
                 min_iteration_time: Optional[int],
                 max_invocation_time: Optional[int], ignore_timeouts, parallel_interference_factor,
                 execute_exclusively, retries_after_failure, env: Optional[Mapping],
                 denoise: Denoise,
                 invocations_override: Optional[int], iterations_override: Optional[int]):
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
        self.denoise = denoise

        self.invocations_override = invocations_override
        self.iterations_override = iterations_override

    def __eq__(self, other):
        return self is other or (
            isinstance(other, self.__class__) and
            self.invocations == other.invocations and
            self.iterations == other.iterations and
            self.warmup == other.warmup and

            self.min_iteration_time == other.min_iteration_time and
            self.max_invocation_time == other.max_invocation_time and
            self.ignore_timeouts == other.ignore_timeouts and
            self.parallel_interference_factor == other.parallel_interference_factor and
            self.execute_exclusively == other.execute_exclusively and
            self.retries_after_failure == other.retries_after_failure and
            self.env == other.env and
            self.denoise == other.denoise and

            self.invocations_override == other.invocations_override and
            self.iterations_override == other.iterations_override)

    # pylint: disable-next=too-many-return-statements
    def __lt__(self, other):
        if self is other:
            return False

        if self.invocations != other.invocations:
            return self.invocations < other.invocations

        if self.iterations != other.iterations:
            return self.iterations < other.iterations

        if self.warmup != other.warmup:
            return self.warmup < other.warmup

        if self.min_iteration_time != other.min_iteration_time:
            return self.min_iteration_time < other.min_iteration_time

        if self.max_invocation_time != other.max_invocation_time:
            return self.max_invocation_time < other.max_invocation_time

        if self.ignore_timeouts != other.ignore_timeouts:
            return self.ignore_timeouts < other.ignore_timeouts

        if self.parallel_interference_factor != other.parallel_interference_factor:
            return self.parallel_interference_factor < other.parallel_interference_factor

        if self.execute_exclusively != other.execute_exclusively:
            return self.execute_exclusively < other.execute_exclusively

        if self.retries_after_failure != other.retries_after_failure:
            return self.retries_after_failure < other.retries_after_failure

        if self.env != other.env:
            return _lt_of_env_dict(self.env, other.env)

        if self.denoise != other.denoise:
            return self.denoise < other.denoise

        if self.invocations_override != other.invocations_override:
            return self.invocations_override < other.invocations_override

        return self.iterations_override < other.iterations_override

    def __hash__(self):
        return hash((self.invocations, self.iterations, self.warmup,
                     self.min_iteration_time, self.max_invocation_time,
                     self.ignore_timeouts, self.parallel_interference_factor,
                     self.execute_exclusively, self.retries_after_failure,
                     tuple(sorted(self.env.items())) if self.env else None, self.denoise,
                     self.invocations_override, self.iterations_override))

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

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ExpRunDetails":
        return ExpRunDetails(data.get("invocations", None),
                             data.get("iterations", None),
                             data.get("warmup", None),
                             data.get("minIterationTime", None),
                             data.get("maxInvocationTime", None),
                             data.get("ignore_timeouts", None),
                             data.get("parallel_interference_factor", None),
                             data.get("execute_exclusively", None),
                             data.get("retries_after_failure", None),
                             data.get("env", None),
                             Denoise.from_dict(data.get("denoise", None)),
                             data.get("invocations_override", None),
                             data.get("iterations_override", None))

    def as_dict(self):
        result = {}

        if self.invocations is not None:
            result["invocations"] = self.invocations

        if self.iterations is not None:
            result["iterations"] = self.iterations

        if self.warmup is not None:
            result["warmup"] = self.warmup

        if self.min_iteration_time is not None:
            result["minIterationTime"] = self.min_iteration_time

        if self.max_invocation_time is not None:
            result["maxInvocationTime"] = self.max_invocation_time

        if self.ignore_timeouts is not None:
            result["ignore_timeouts"] = self.ignore_timeouts

        if self.parallel_interference_factor is not None:
            result["parallel_interference_factor"] = self.parallel_interference_factor

        if self.execute_exclusively is not None:
            result["execute_exclusively"] = self.execute_exclusively

        if self.retries_after_failure is not None:
            result["retries_after_failure"] = self.retries_after_failure

        if self.env is not None:
            result["env"] = self.env

        if self.denoise is not None:
            result["denoise"] = self.denoise.as_dict()

        if self.invocations_override is not None:
            result["invocations_override"] = self.invocations_override

        if self.iterations_override is not None:
            result["iterations_override"] = self.iterations_override

        if not result:
            return None

        return result
