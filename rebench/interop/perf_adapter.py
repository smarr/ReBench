from .adapter import GaugeAdapter
from ..model.profile_data import ProfileData


class PerfAdapter(GaugeAdapter):

    def __init__(self, debug=False):
        super(PerfAdapter, self).__init__(False)
        self._debug = debug

    def parse_data(self, data, run_id, invocation):
        profilers = run_id.benchmark.suite.executor.profiler
        assert len(profilers) == 1

        profiler = profilers[0]  # TODO: needs changing when we support multiple profilers
        json = profiler.process_profile(run_id, self._debug)

        return [ProfileData(run_id, json, run_id.iterations, invocation)]

