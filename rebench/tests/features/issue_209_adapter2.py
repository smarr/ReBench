from re import compile as re_compile

from rebench.interop.adapter   import GaugeAdapter, OutputNotParseable,\
    ResultsIndicatedAsInvalid
from rebench.model.data_point  import DataPoint
from rebench.model.measurement import Measurement


class AbstractAdapter(GaugeAdapter):
    """Performance reader for the test case and the definitions
       in test/test.conf
    """

    __test__ = False  # This is not a test class
    re_time = re_compile(r"RESULT-(\w+):\s*(\d+\.\d+)")

    def __init__(self, include_faulty, executor):
        super(AbstractAdapter, self).__init__(include_faulty, executor)
        self._other_error_definitions = [re_compile("FAILED")]

    def _make_measurement(self, run_id, invocation, iteration, value, criterion):
        return Measurement(invocation, iteration, value, 'ms', run_id, criterion)

    def parse_data(self, data, run_id, invocation):
        iteration = 1
        data_points = []
        current = DataPoint(run_id)

        for line in data.split("\n"):
            if self.check_for_error(line):
                raise ResultsIndicatedAsInvalid(
                    "Output of bench program indicated error.")

            match = MyTestAdapter.re_time.match(line)
            if match:
                measure = self._make_measurement(run_id, invocation, iteration,
                                                 float(match.group(2)), match.group(1))
                current.add_measurement(measure)

                if measure.is_total():
                    data_points.append(current)
                    current = DataPoint(run_id)
                    iteration += 1

        if not data_points:
            raise OutputNotParseable(data)

        return data_points


class MyTestAdapter(AbstractAdapter):
    def _make_measurement(self, run_id, invocation, iteration, value, criterion):
        return Measurement(invocation, iteration, value + 1, 'ms', run_id, criterion)


class MyTestAdapter2(AbstractAdapter):
    def _make_measurement(self, run_id, invocation, iteration, value, criterion):
        return Measurement(invocation, iteration, value + 2, 'ms', run_id, criterion)
