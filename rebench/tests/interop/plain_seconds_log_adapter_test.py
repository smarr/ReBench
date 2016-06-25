# Copyright (c) 2016 Stefan Marr <http://www.stefan-marr.de/>
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
from unittest import TestCase

from ...interop.adapter      import OutputNotParseable
from ...interop.plain_seconds_log_adapter import PlainSecondsLogAdapter


class PlainSecondsAdapterTest(TestCase):

    def test_acquire_command(self):
        pa = PlainSecondsLogAdapter(False)
        cmd = pa.acquire_command("FOO")
        self.assertEqual("FOO", cmd)

    def test_parse_data(self):
        data = """100
50
1"""
        pa = PlainSecondsLogAdapter(False)
        d = pa.parse_data(data, None)
        self.assertEqual(3, len(d))

        self.assertEqual(1, len(d[0].get_measurements()))
        self.assertEqual(100000, d[0].get_total_value())

        self.assertEqual(1, len(d[1].get_measurements()))
        self.assertEqual(50000, d[1].get_total_value())

        self.assertEqual(1, len(d[2].get_measurements()))
        self.assertEqual(1000, d[2].get_total_value())

    def test_parse_no_data(self):
        ta = PlainSecondsLogAdapter(False)
        self.assertRaises(OutputNotParseable, ta.parse_data, "", None)
