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

from setuptools import setup, find_packages
from rebench import __version__ as rebench_version

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='ReBench',
      version=rebench_version,
      description='Execute and document benchmarks reproducibly.',
      long_description=long_description,
      long_description_content_type="text/markdown",
      author='Stefan Marr',
      author_email='rebench@stefan-marr.de',
      url='https://github.com/smarr/ReBench',
      packages=find_packages(exclude=['*.tests']),
      package_data={'rebench': ['rebench-schema.yml']},
      install_requires=[
          'PyYAML>=3.12',
          'pykwalify>=1.6.1',
          'humanfriendly>=8.0',
          'py-cpuinfo==6.0.0',
          'psutil>=5.6.7'
      ],
      entry_points = {
          'console_scripts' : ['rebench = rebench.rebench:main_func']
      },
      test_suite = 'rebench.tests',
      license = 'MIT'
)
