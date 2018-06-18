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


class ExpVariables(object):

    @classmethod
    def compile(cls, config, defaults):
        input_sizes = config.get('input_sizes', defaults.input_sizes)
        cores = config.get('cores', defaults.cores)
        variable_values = config.get('variable_values', defaults.variable_values)
        return ExpVariables(input_sizes, cores, variable_values)

    @classmethod
    def empty(cls):
        return ExpVariables([''], [1], [''])

    def __init__(self, input_sizes, cores, variable_values):
        self._input_sizes = input_sizes
        self._cores = cores
        self._variable_values = variable_values

    @property
    def input_sizes(self):
        return self._input_sizes

    @property
    def cores(self):
        return self._cores

    @property
    def variable_values(self):
        return self._variable_values
