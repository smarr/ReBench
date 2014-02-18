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


class Reporting(object):
    
    def __init__(self, raw_config):
        self._csv_file   = raw_config.get('csv_file',   None)
        self._csv_locale = raw_config.get('csv_locale', None)
        self._csv_raw    = raw_config.get('csv_raw',    None)
        
        self._confidence_level = raw_config.get('confidence_level', 0.95)
    
    @property
    def csv_file(self):
        return self._csv_file
    
    @property
    def csv_locale(self):
        return self._csv_locale
    
    @property
    def csv_raw(self):
        return self._csv_raw
    
    @property
    def confidence_level(self):
        return self._confidence_level

    def combined(self, raw_config):
        rep = Reporting({})
        rep._csv_file   = raw_config.get('csv_file',   self._csv_file)
        rep._csv_locale = raw_config.get('csv_locale', self._csv_locale)
        rep._csv_raw    = raw_config.get('csv_raw',    self._csv_raw)
        
        rep._confidence_level = raw_config.get('confidence_level',
                                               self._confidence_level)

        return rep
