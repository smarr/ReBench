# Copyright (c) 2009-2014 Stefan Marr <http://www.stefan-marr.de/>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
import os
import subprocess
import unittest

from .. import subprocess_with_timeout as sub


class SubprocessTimeoutTest(unittest.TestCase):
    """Test the support for execution of programs with timeouts"""
    
    def setUp(self):
        self._path = os.path.dirname(os.path.realpath(__file__))

    def test_normal_exec_no_timeout(self):
        cmdline = "sleep 1; echo Done"
        (return_code, output, err) = sub.run(cmdline, cwd=self._path,
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.STDOUT,
                                             shell=True, timeout=10)

        self.assertEqual(       0, return_code)
        self.assertEqual("Done\n",      output)
        self.assertEqual(    None,         err)

    def test_exec_with_timeout(self):
        cmdline = "sleep 100; echo Done"
        (return_code, output, err) = sub.run(cmdline, cwd=self._path,
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.STDOUT,
                                             shell=True, timeout=1)
        
        self.assertEqual(-9,   return_code)
        self.assertEqual("",   output)
        self.assertEqual("", err)
    
    def test_exec_with_timeout_python_interpreter(self):
        cmdline = "python -c \"while True: pass\""
        (return_code, output, err) = sub.run(cmdline, cwd=self._path,
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.STDOUT,
                                             shell=True, timeout=5)
        
        self.assertEqual(-9, return_code)
        self.assertEqual("", output)
        self.assertEqual("", err)
    
    
def test_suite():
    return unittest.makeSuite(SubprocessTimeoutTest)

if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')
