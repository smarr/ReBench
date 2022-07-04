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


def prefer_important(val, default):
    if val is None:
        return default
    if is_marked_important(val):
        return val
    if is_marked_important(default):
        return default
    return val


def is_marked_important(val):
    if isinstance(val, int):
        return False
    return str(val)[-1] == "!"


def remove_important(val):
    if val is None:
        return None

    if isinstance(val, int):
        return val

    if val[-1] == "!":
        return int(val[:-1])
    return int(val)


def none_or_int(value):
    if value:
        return int(value)
    return value


def none_or_float(value):
    if value:
        return float(value)
    return value


def none_or_bool(value):
    if value:
        return bool(value)
    return value


def none_or_dict(value):
    if value:
        assert isinstance(value, dict)
    return value


def value_with_optional_details(value, default_details=None):
    if isinstance(value, dict):
        assert len(value) == 1
        (value, details) = list(value.items())[0]
    else:
        details = default_details

    return value, details
