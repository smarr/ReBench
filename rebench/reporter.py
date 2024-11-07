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
from time import time
from operator import itemgetter
import json
import re

from http.client import HTTPException
from urllib.request import urlopen
from urllib.parse import urlencode
from humanfriendly.tables import format_pretty_table
from humanfriendly.terminal import ansi_wrap

from rebench.model.run_id import RunId


class Reporter(object):

    def __init__(self):
        self._job_completion_reported = False

    def run_failed(self, _run_id, _cmdline, _return_code, _output):
        pass

    def run_completed(self, run_id, statistics, cmdline):
        pass

    def report_job_completed(self, run_ids):
        pass

    def job_completed(self, run_ids):
        if not self._job_completion_reported:
            self.report_job_completed(run_ids)
            self._job_completion_reported = True

    def set_total_number_of_runs(self, num_runs):
        pass

    def start_run(self, run_id):
        pass


class TextReporter(Reporter):

    def __init__(self):
        super(TextReporter, self).__init__()
        self.expected_columns = ['Benchmark', 'Executor', 'Suite', 'Extra', 'Core', 'Size', 'Var',
             'Tag', '#Samples', 'Mean (ms)']

    @staticmethod
    def _path_to_string(path):
        out = [path[0].as_simple_string()]
        for item in path[1:]:
            if item:
                out.append(str(item))
        return " ".join(out) + " "

    def _generate_all_output(self, run_ids: set[RunId]):
        """
        Collect all values to generate overview table.

        Though, we want the table to be as compact as possible.
        So, we do identify columns that repeat the same value, and strip them from the table
        to output them before as summary details.

        We handle tables with <=4 rows differently and show all columns in the table.

        We also show always the last column, which is the mean of the total values.
        """
        column_value_sets: list[set[str]] = [set() for _ in self.expected_columns]

        rows = []

        for run_id in run_ids:
            mean = run_id.get_mean_of_totals()
            num_samples = run_id.get_number_of_data_points()
            out = run_id.as_str_list(0)
            out[-1] = num_samples # can just overwrite the last value, which is the run_id_id
            if num_samples == 0:
                out.append("Failed")
            else:
                out.append(int(round(mean, 0)))

            for i, v in enumerate(out):
                column_value_sets[i].add(v)
            rows.append(out)

        sorted_rows = sorted(rows, key=itemgetter(2, 1, 3, 4, 5, 6, 7))

        if len(sorted_rows) <= 4:
            return sorted_rows, self.expected_columns, None

        return self._filter_columns(sorted_rows, column_value_sets)

    def _filter_columns(self, sorted_rows, column_value_sets):
        assert self.expected_columns[-1] == "Mean (ms)"
        last_column_idx = len(self.expected_columns) - 1

        summary = []
        used_cols = []
        column_idxs_to_be_deleted = []

        for i, values in enumerate(column_value_sets):
            if len(values) > 1 or i == last_column_idx:
                used_cols.append(self.expected_columns[i])
            else:
                column_idxs_to_be_deleted.insert(0, i)
                summary.append([self.expected_columns[i], values.pop()])

        for row in sorted_rows:
            for i in column_idxs_to_be_deleted:
                del row[i]

        return sorted_rows, used_cols, summary


class CliReporter(TextReporter):
    """ Reports to standard out using the logging framework """

    def __init__(self, executes_verbose, ui):
        super(CliReporter, self).__init__()
        self._num_runs = None
        self.ui = ui
        self._runs_completed = 0
        self._start_time = None
        self._runs_remaining = 0
        self._executes_verbose = executes_verbose

    def run_failed(self, run_id, cmdline, return_code, cmd_output):
        pass

    def run_completed(self, run_id, statistics, cmdline):
        self._runs_completed += 1
        self._runs_remaining -= 1

    def report_job_completed(self, run_ids):
        rows, used_cols, summary = self._generate_all_output(run_ids)
        self.ui.output("\n")
        if summary:
            self.ui.output(ansi_wrap(" Result Summary of Uniform Values", bold=True))
            self.ui.output(format_pretty_table(summary, ['Property', 'Value'],
                                               vertical_bar='', horizontal_bar=''))
        self.ui.output(format_pretty_table(rows, used_cols, vertical_bar=''))

    def set_total_number_of_runs(self, num_runs):
        self._num_runs = num_runs
        self._runs_remaining = num_runs


class CodespeedReporter(Reporter):
    """
    This report will report the recorded data on the completion of the job
    to the configured Codespeed instance.
    """

    def __init__(self, cfg, ui):
        super(CodespeedReporter, self).__init__()
        self._cfg = cfg
        self._incremental_report = self._cfg.report_incrementally
        self._cache_for_seconds = 30
        self._cache = {}
        self._last_send = time()
        self.ui = ui

    def run_completed(self, run_id, statistics, cmdline):
        if not self._incremental_report:
            return

        # ok, talk to codespeed immediately
        self._cache[run_id] = self._format_for_codespeed(run_id, statistics)

        if time() - self._last_send >= self._cache_for_seconds:
            self._send_and_empty_cache()

    def _send_and_empty_cache(self):
        if not self._cache:
            return

        if len(self._cache) == 1:
            run_id = list(self._cache.keys())[0]
        else:
            run_id = None
        self._send_to_codespeed(list(self._cache.values()), run_id)
        self._cache = {}

    def _result_data_template(self):
        # all None values have to be filled in
        return {
            "commitid": self._cfg.commit_id,
            "project": self._cfg.project,
            "executable": None,
            "benchmark": None,
            "environment": self._cfg.environment,
            "branch": self._cfg.branch,
            "result_value": None,
            "std_dev": None,
            "max": None,
            "min": None,
        }

    @staticmethod
    def _beautify_benchmark_name(name):
        """
        Currently just remove all bench, or benchmark strings.
        """
        replace = re.compile("bench(mark)?", re.IGNORECASE)
        return replace.sub("", name)

    def _format_for_codespeed(self, run_id, stats=None):
        result = self._result_data_template()

        if stats and not run_id.run_failed():
            result["min"] = stats.min
            result["max"] = stats.max
            result["std_dev"] = stats.std_dev
            result["result_value"] = stats.mean
        else:
            result["result_value"] = -1

        result["executable"] = self._cfg.executable or run_id.benchmark.suite.executor.name

        if run_id.benchmark.codespeed_name:
            name = run_id.benchmark.codespeed_name
        else:
            name = (self._beautify_benchmark_name(run_id.benchmark.name)
                    + " (%(cores)s cores, %(input_sizes)s %(extra_args)s)")

        # TODO: this is incomplete:
        name = name % {'cores'       : run_id.cores_as_str,
                       'input_sizes' : run_id.input_size_as_str,
                       'extra_args'  : run_id.benchmark.extra_args}

        result["benchmark"] = name

        return result

    def _send_payload(self, payload):
        with urlopen(self._cfg.url, payload) as socket:
            response = socket.read()
            return response

    def _send_to_codespeed(self, results, run_id):
        payload = urlencode({"json": json.dumps(results)})

        try:
            self._send_payload(payload)
        except (IOError, HTTPException):
            # sometimes Codespeed fails to accept a request because something
            # is not yet properly initialized, let's try again for those cases
            try:
                response = self._send_payload(payload)
                self.ui.verbose_error_info("Sent %d results to Codespeed, response was: %s\n"
                                            % (len(results), response))
            except (IOError, HTTPException) as error:
                envs = list({i['environment'] for i in results})
                projects = list({i['project'] for i in results})
                benchmarks = list({i['benchmark'] for i in results})
                executables = list({i['executable'] for i in results})
                msg = ("{ind}Data\n"
                       + "{ind}{ind}environments: %s\n"
                       + "{ind}{ind}projects: %s\n"
                       + "{ind}{ind}benchmarks: %s\n"
                       + "{ind}{ind}executables: %s\n") % (
                           envs, projects, benchmarks, executables)

                self.ui.error(
                    "{ind}Error: Reporting to Codespeed failed.\n"
                    + "{ind}{ind}" + str(error) + "\n"
                    + "{ind}{ind}This is most likely caused by either a wrong URL in the\n"
                    + "{ind}{ind}config file, or an environment not configured in Codespeed.\n"
                    + "{ind}{ind}URL: " + self._cfg.url + "\n"
                    + "{ind}{ind}" + msg + "\n", run_id)

    def _prepare_result(self, run_id):
        return self._format_for_codespeed(run_id, run_id.statistics)

    def report_job_completed(self, run_ids):
        if self._incremental_report:
            # send remaining items from cache
            self._send_and_empty_cache()
            return

        results = [self._prepare_result(run_id) for run_id in run_ids]

        if len(run_ids) == 1:
            run_id = run_ids[0]
        else:
            run_id = None

        # now, send them of to codespeed
        self._send_to_codespeed(results, run_id)
