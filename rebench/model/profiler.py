from ..interop.perf_parser import PerfParser
from ..subprocess_with_timeout import run
from ..ui import UIError


class Profiler(object):

    @classmethod
    def compile(cls, profiler_data):
        profilers = []
        if profiler_data is None:
            return profilers

        for k, v in profiler_data.items():
            if k == "perf":
                perf = PerfProfiler(k, v)
                profilers.append(perf)
            else:
                raise Exception("Not yet supported profiler type: " + k)
        return profilers

    def __init__(self, name):
        self.name = name


class PerfProfiler(Profiler):

    def __init__(self, name, cfg):
        super(PerfProfiler, self).__init__(name)
        self.record_args = cfg.get('record_args')
        self.report_args = cfg.get('report_args')
        self.command = "perf"

    def _construct_report_cmdline(self):
        return self.command + " " + self.report_args

    def process_profile(self, run_id, verbose):
        cmdline = self._construct_report_cmdline()
        (return_code, output, _) = run(cmdline, cwd=run_id.location, shell=True,
                                       verbose=verbose)

        if return_code != 0:
            raise UIError(
                "perf failed with error code when processing the profile to create a report: "
                + str(return_code), None)

        parser = PerfParser()
        parser.parse_lines(output.split("\n"))
        return parser.json()
