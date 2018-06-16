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
import sys

from humanfriendly.compat import coerce_string
from humanfriendly.terminal import terminal_supports_colors, ansi_wrap, auto_encode

DETAIL_INDENT = "\n    "


def warning_low_priority(text, *args, **kw):
    text = coerce_string(text)
    if terminal_supports_colors(sys.stderr):
        text = ansi_wrap(text, color='magenta')
    auto_encode(sys.stderr, text + '\n', *args, **kw)


class UIError(Exception):

    def __init__(self, message, exception):
        super(UIError, self).__init__()
        self._message = message
        self._exception = exception

    @property
    def message(self):
        return self._message

    @property
    def source_exception(self):
        return self._exception
