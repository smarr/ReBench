from .denoise import Denoise
from ..denoise_client import construct_denoise_exec_prefix
from ..interop.adapter import ExecutionDeliveredNoResults
from ..interop.perf_parser import PerfParser
from ..subprocess_with_timeout import run


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
        self.record_args: str = cfg.get("record_args") + " --output=profile.perf "
        self.report_args: str = cfg.get("report_args") + " --input=profile.perf "
        self.command: str = "perf"

    def _construct_report_cmdline_and_env(self, executor, run_id):
        # need to use sudo, otherwise, the profile.perf file won't be accessible
        cmd = ""
        env = run_id.env
        if executor.use_denoise:
            cmd, env = construct_denoise_exec_prefix(run_id.env, True, Denoise.system_default())

        return cmd + self.command + " " + self.report_args, env

    def process_profile(self, run_id, executor):
        cmdline, env = self._construct_report_cmdline_and_env(executor, run_id)
        (return_code, output, _) = run(cmdline, env, cwd=run_id.location, shell=True,
                                       verbose=executor.debug)

        if return_code != 0:
            raise ExecutionDeliveredNoResults(
                "perf failed with error code when processing the profile to create a report: "
                + str(return_code))

        parser = PerfParser()
        parser.parse_lines(output.split("\n"))
        return parser.to_json()
