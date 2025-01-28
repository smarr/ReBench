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
import os
import stat

from setuptools import setup, find_packages
from setuptools.command.install import install
from rebench import __version__ as rebench_version

with open("README.md", "r") as fh:
    long_description = fh.read()

class InstallAndSetDenoisePermissions(install):
    def run(self):
        install.run(self)
        install_path = os.path.join(self.install_lib, "rebench")
        denoise_path = os.path.join(install_path, "denoise.py")
        if os.path.exists(denoise_path):
            st = os.stat(denoise_path)
            os.chmod(denoise_path, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

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
          'PyYAML>=6.0',
          'pykwalify>=1.8.0',
          'humanfriendly>=10.0',
          'py-cpuinfo==9.0.0',
          'psutil>=5.9.5'
      ],
      test_require=[
          'pytest>=7.2.2'
      ],
      entry_points={
          'console_scripts': [
              'rebench = rebench.rebench:main_func',
              'rebench-denoise = rebench.denoise:main_func'
          ]
      },
      scripts=['rebench/denoise.py'],
      cmdclass={'install': InstallAndSetDenoisePermissions},
      test_suite='rebench.tests',
      license='MIT'
)
