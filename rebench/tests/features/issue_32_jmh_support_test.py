# Copyright (c) 2009-2014 Stefan Marr <http://www.stefan-marr.de/>
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
from os.path  import dirname, realpath
from unittest import TestCase

from ...interop.jmh_adapter import JMHAdapter


class Issue32JMHSupport(TestCase):
    """
    Add support for JMH, a Java benchmarking harness.
    """

    def setUp(self):
        self._path = dirname(realpath(__file__))
        with open(self._path + "/issue_32_jmh.data") as data_file:
            self._data = data_file.read()

    def test_parsing(self):
        adapter = JMHAdapter(False)
        data_points = adapter.parse_data(self._data, None)

        self.assertEqual(4 * 20, len(data_points))

        for i in range(0, 60):
            self.assertAlmostEqual(830000, data_points[i].get_total_value(),
                                   delta=60000)
        for i in range(60, 80):
            self.assertAlmostEqual(86510, data_points[i].get_total_value(),
                                   delta=4000)
