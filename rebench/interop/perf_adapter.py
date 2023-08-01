from .adapter import GaugeAdapter
from ..model.profile_data import ProfileData


class PerfAdapter(GaugeAdapter):

    @staticmethod
    def _get_profiler(run_id):
        profilers = run_id.benchmark.suite.executor.profiler
        assert len(profilers) == 1

        return profilers[0]  # TODO: needs changing when we support multiple profilers

    def parse_data(self, data, run_id, invocation):
        profiler = self._get_profiler(run_id)
        json = profiler.process_profile(run_id, self._executor)

        return [ProfileData(run_id, json, run_id.iterations, invocation)]

    def acquire_command(self, run_id):
        profiler = self._get_profiler(run_id)
        return (profiler.command + " " + profiler.record_args + " " +
                run_id.cmdline_for_next_invocation())
