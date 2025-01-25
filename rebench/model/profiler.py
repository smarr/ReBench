from typing import Mapping, Optional, Sequence

from .denoise import Denoise
from ..denoise_client import construct_denoise_exec_prefix
from ..interop.adapter import ExecutionDeliveredNoResults
from ..interop.perf_parser import PerfParser
from ..subprocess_with_timeout import run


class Profiler(object):

    @classmethod
    def compile(cls, profiler_data) -> Optional[Sequence["Profiler"]]:
        profilers = []
        if not profiler_data:
            return None

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

    def as_dict(self):
        raise NotImplementedError("as_dict() must be implemented by subclasses")

    @classmethod
    def from_dict(cls, data: Optional[list[Mapping]]) -> Optional[list["Profiler"]]:
        if not data:
            return None

        result: list["Profiler"] = []
        for p in data:
            ## we keep it simple for now, because we only have PerfProfiler
            result.append(PerfProfiler.from_dict(p))
        return result

_PERF_OUT = " --output=profile.perf "
_PERF_IN = " --input=profile.perf "

class PerfProfiler(Profiler):

    def __init__(self, name, cfg: Mapping):
        super(PerfProfiler, self).__init__(name, "Perf")
        self.record_args: str = cfg.get("record_args", "") + _PERF_OUT
        self.report_args: str = cfg.get("report_args", "") + _PERF_IN
        self.command: str = "perf"

    @classmethod
    def from_dict(cls, data: Mapping) -> "PerfProfiler": # type: ignore[override]
        return PerfProfiler(data["name"], data)

    def as_dict(self):
        record = self.record_args.replace(_PERF_OUT, "")
        report = self.report_args.replace(_PERF_IN, "")
        result = { "name": self.name }

        if record:
            result["record_args"] = record
        if report:
            result["report_args"] = report

        return result

    def __eq__(self, other):
        return self is other or (
                isinstance(other, self.__class__) and
                self.name == other.name and
                self.record_args == other.record_args and
                self.report_args == other.report_args)

    def __hash__(self):
        return hash((self.name, self.record_args, self.report_args))

    def __lt__(self, other):
        if self.name != other.name:
            return self.name < other.name

        if self.record_args != other.record_args:
            return self.record_args < other.record_args

        return self.report_args < other.report_args

    def _construct_report_cmdline(self, executor, run_id):
        # need to use sudo, otherwise, the profile.perf file won't be accessible
        possible_settings = run_id.denoise.possible_settings(executor.get_denoise_initial())
        if possible_settings.needs_denoise():
            cmd = construct_denoise_exec_prefix(run_id.env, True, Denoise.system_default())
        else:
            cmd = ""

        return cmd + self.command + " " + self.report_args

    def process_profile(self, run_id, executor):
        cmdline = self._construct_report_cmdline(executor, run_id)
        (return_code, output, _) = run(cmdline, run_id.env, cwd=run_id.location, shell=True,
                                       verbose=executor.debug)

        if return_code != 0:
            raise ExecutionDeliveredNoResults(
                "perf failed with error code when processing the profile to create a report: "
                + str(return_code))

        parser = PerfParser()
        parser.parse_lines(output.split("\n"))
        return parser.to_json()
