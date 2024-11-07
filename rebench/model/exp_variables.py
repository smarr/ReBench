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
from typing import Mapping


class ExpVariables(object):

    @classmethod
    def compile(cls, config: dict, defaults: "ExpVariables") -> "ExpVariables":
        input_sizes = config.get("input_sizes", defaults.input_sizes)
        cores = config.get("cores", defaults.cores)
        variable_values = config.get("variable_values", defaults.variable_values)
        tags = config.get("tags", defaults.tags)
        return ExpVariables(input_sizes, cores, variable_values, tags)

    @classmethod
    def empty(cls):
        return ExpVariables([""], [1], [""], [None])

    def __init__(
        self, input_sizes: list, cores: list, variable_values: list, tags: list
    ):
        self.input_sizes = input_sizes
        self.cores = cores
        self.variable_values = variable_values
        self.tags = tags

    @classmethod
    def from_dict(cls, config: dict) -> "ExpVariables":
        empty = ExpVariables.empty()
        return ExpVariables(
            config.get("input_sizes", empty.input_sizes),
            config.get("cores", empty.cores),
            config.get("variable_values", empty.variable_values),
            config.get("tags", empty.tags),
        )

    def as_dict(self) -> Mapping:
        return {
            "input_sizes": self.input_sizes,
            "cores": self.cores,
            "variable_values": self.variable_values,
            "tags": self.tags,
        }

    def __eq__(self, other):
        return self is other or (
            isinstance(other, self.__class__)
            and self.input_sizes == other.input_sizes
            and self.cores == other.cores
            and self.variable_values == other.variable_values
            and self.tags == other.tags
        )

    def __lt__(self, other):
        if self.input_sizes != other.input_sizes:
            return self.input_sizes < other.input_sizes
        if self.cores != other.cores:
            return self.cores < other.cores
        if self.variable_values != other.variable_values:
            return self.variable_values < other.variable_values
        return self.tags < other.tags

    def __hash__(self):
        return hash(
            (
                tuple(self.input_sizes),
                tuple(self.cores),
                tuple(self.variable_values),
                tuple(self.tags),
            )
        )
