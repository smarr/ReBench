# ReBench: Execute and document benchmarks reproducibly.
#
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

from setuptools import setup
from rebench import ReBench

rebench = ReBench()

setup(name='ReBench',
      version=rebench.version,
      description='Execute and document benchmarks reproducibly.',
      author='Stefan Marr',
      author_email='rebench@stefan-marr.de',
      url='https://github.com/smarr/ReBench',
      packages=['rebench', 'rebench.model', 'rebench.interop', 'rebench.libs'],
      install_requires=[
          'PyYAML>=3.08'
      ],
      entry_points = {
          'console_scripts' : ['rebench = rebench:main_func']
      },
      extras_require = {
          'SciPy': ['scipy>=0.8.0'],
          'IRC' :  ['irc>=8.9.1']
      },
      test_suite = 'rebench.tests',
      license = 'MIT'
)
