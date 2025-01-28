# Copyright (c) 2009-2025 Stefan Marr <https://www.stefan-marr.de/>
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
from ...configurator import Configurator, load_config
from ...executor import Executor
from ...persistence import DataStore

from ..rebench_test_case import ReBenchTestCase


class EnvQuoteTest(ReBenchTestCase):

    def setUp(self):
        super(EnvQuoteTest, self).setUp()
        self._set_path(__file__)

    def test_execution_should_recognize_invalid_run_and_continue_normally(self):
        cnf = Configurator(
            load_config(self._path + "/env_quote.conf"),
            DataStore(self.ui),
            self.ui,
            data_file=self._tmp_file,
        )
        runs = list(cnf.get_runs())
        self.assertEqual(runs[0].get_number_of_data_points(), 0)

        ex = Executor([runs[0]], False, self.ui)
        ex.execute()

        self.assertEqual(runs[0].get_number_of_data_points(), 1)
