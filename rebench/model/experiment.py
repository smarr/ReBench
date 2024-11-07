# Copyright (c) 2009-2018 Stefan Marr <http://www.stefan-marr.de/>
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
from . import value_with_optional_details
from .benchmark import Benchmark
from .benchmark_suite import BenchmarkSuite
from .exp_run_details import ExpRunDetails
from .exp_variables import ExpVariables
from .reporting import Reporting


class Experiment(object):

    @classmethod
    def compile(cls, name, exp, configurator):
        action = exp.get("action")
        description = exp.get("description")
        desc = exp.get("desc")
        if action == "profile":
            data_file = exp.get("data_file") or configurator.data_file + ".profiles"
        else:
            data_file = exp.get("data_file") or configurator.data_file

        reporting = Reporting.compile(exp.get('reporting', {}), configurator.reporting,
                                      configurator.options, configurator.ui)

        run_details = ExpRunDetails.compile(exp, configurator.base_run_details)
        variables = ExpVariables.compile(exp, configurator.base_variables)

        executions = exp.get("executions")
        suites = exp.get("suites")

        env = exp.get("env")

        return Experiment(name, description or desc, action, env, data_file, reporting,
                          run_details, variables, configurator, executions, suites)

    def __init__(self, name, description, action, env, data_file, reporting, run_details,
                 variables, configurator, executions, suites):
        self.name = name
        self._description = description
        self._action = action

        self._run_details = run_details
        self._variables = variables
        self._env = env
        self._reporting = reporting

        self._data_store = configurator.data_store
        self._persistence = self._data_store.get(data_file, configurator, action)

        self._suites = self._compile_executors_and_benchmark_suites(
            executions, suites, configurator)
        self._benchmarks = self._compile_benchmarks()
        self.runs = self._compile_runs(configurator)

    def _compile_runs(self, configurator):
        runs = set()

        # pylint: disable-next=too-many-nested-blocks
        for bench in self._benchmarks:
            if not configurator.run_filter.applies_to_bench(bench):
                continue
            variables = bench.variables
            for cores in variables.cores:
                for input_size in variables.input_sizes:
                    for var_val in variables.variable_values:
                        for tag in variables.tags:
                            if not configurator.run_filter.applies_to_tag(tag):
                                continue
                            run = self._data_store.create_run_id(
                                bench, cores, input_size, var_val, tag, configurator.machine)
                            runs.add(run)
                            run.add_reporting(self._reporting)
                            run.add_persistence(self._persistence)
        return runs

    def _compile_executors_and_benchmark_suites(self, executions, suites, configurator):
        # we now assemble the executors and the benchmark suites
        results = []
        for executor_cfg in executions:
            executor_name, executor_details = value_with_optional_details(executor_cfg)

            run_details = self._run_details
            variables = self._variables

            if executor_details:
                run_details = ExpRunDetails.compile(executor_details, run_details)
                variables = ExpVariables.compile(executor_details, variables)
                suites_for_executor = executor_details.get("suites", suites)
            else:
                suites_for_executor = suites

            executor = configurator.get_executor(
                executor_name, run_details, variables, self._action)

            for suite_name in suites_for_executor:
                suite = BenchmarkSuite.compile(
                    suite_name, configurator.get_suite(suite_name), executor,
                    configurator.deduplicated_build_commands)
                results.append(suite)

        return results

    def _compile_benchmarks(self):
        bench_cfgs = []
        for suite in self._suites:
            for bench in suite.benchmarks_config:
                bench_cfgs.append(Benchmark.compile(bench, suite))
        return bench_cfgs
