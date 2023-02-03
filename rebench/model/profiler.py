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
                raise NotImplementedError("Not yet supported profiler type: " + k)
        return profilers

    def __init__(self, name, gauge_name):
        self.name = name
        self.gauge_adapter_name = gauge_name


class PerfProfiler(Profiler):

    def __init__(self, name, cfg):
        super(PerfProfiler, self).__init__(name, "Perf")
        self.record_args = cfg.get('record_args') + " --output=profile.perf "
        self.report_args = cfg.get('report_args') + " --input=profile.perf "
        self.command = "perf"

    def _construct_report_cmdline(self, executor):
        # need to use sudo, otherwise, the profile.perf file won't be accessible
        cmd = ""
        if executor.use_denoise:
            cmd += "sudo rebench-denoise --without-nice --without-shielding exec -- "
        return cmd + self.command + " " + self.report_args

    def process_profile(self, run_id, executor):
        cmdline = self._construct_report_cmdline(executor)
        (return_code, output, _) = run(cmdline, run_id.env, cwd=run_id.location, shell=True,
                                       verbose=executor.debug)

        if return_code != 0:
            raise UIError(
                "perf failed with error code when processing the profile to create a report: "
                + str(return_code), None)

        parser = PerfParser()
        parser.parse_lines(output.split("\n"))
        return parser.to_json()
