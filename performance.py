# Copyright (c) 2009 Stefan Marr <http://www.stefan-marr.de/>
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
import re

class Performance:
  """Performance provides a common interface and some helper functionality
     to evaluate the output of benchmarks and to determine measured performance
     values.
  """
  
  # definition of some regular expression to identify erroneous runs
  re_error    = re.compile("Error")
  re_segfault = re.compile("Segmentation fault")
  re_buserror = re.compile("Bus error") 
  
  def acquire_command(self, commmand):
    return command

  def parse_data(self, data):
    pass

  def check_for_error(self, line):
    """Check whether the output line contains one of the common error
       messages. If its an erroneous run, the result has to be discarded.
    """
    if self.re_error.search(line):
      return True
    if self.re_segfault.search(line):
      return True
    if self.re_buserror.search(line):
      return True
    
    return False

class LogPerformance(Performance):
  """LogPerformance is the standard for ReBench.
     It is used to read a simple log format which includes the number of iterations of
     a benchmark and its runtime in microseconds.
  """
  re_logline  = re.compile(r"^(\w*): iterations=([0-9]+) runtime: ([0-9]+)us")

  def parse_data(self, data):      
    for line in data.split("\n"):
      if self.check_for_error(line):
        return None
      m = self.re_logline.match(line)
      if m:
        return float(m.group(3))

class TestPerformance(Performance):
    
    test_data = [45872, 45871, 45868, 45869, 45873,
                 45865, 45869, 45874, 45863, 45873,
                 45872, 45873, 45867, 45872, 45876,
                 45871, 45870, 45870, 45868, 45869,
                 45872, 45873, 45867, 45866, 45869,
                 45875, 45871, 45869, 45870, 45874]
    index = 0
    
    def parse_data(self, data):
        result = self.test_data[self.index]
        self.index = (self.index + 1) % len(self.test_data)
        return result

