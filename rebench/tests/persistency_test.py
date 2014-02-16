import unittest

from datetime import datetime

from rebench.model.run_id           import RunId
from rebench.model.measurement      import Measurement
from rebench.model.benchmark_config import BenchmarkConfig
from rebench.model.benchmark_suite  import BenchmarkSuite
from rebench.model.virtual_machine  import VirtualMachine


class PersistencyTest(unittest.TestCase):

    def test_de_serialization(self):
        vm        = VirtualMachine("MyVM", None, {'path':'','binary':''}, None, [1], None)
        suite     = BenchmarkSuite("MySuite", vm, {'benchmarks':[], 'performance_reader':'', 'command':''})
        bench_cfg = BenchmarkConfig("Test Bench [>", None, suite, vm)


        run_id = RunId(bench_cfg, 1000, 44, 'sdf sdf sdf sdfsf')
        timestamp = datetime.now().replace(microsecond=0)
        measurement = Measurement(2222.2222, 'ms', run_id, 'foobar crit', timestamp)

        serialized = measurement.as_str_list()
        deserialized = Measurement.from_str_list(serialized)

        self.assertEquals(deserialized.criterion, measurement.criterion)
        self.assertEquals(deserialized.value,     measurement.value)
        self.assertEquals(deserialized.unit,      measurement.unit)
        self.assertAlmostEquals(deserialized.timestamp, measurement.timestamp)

        self.assertEquals(deserialized.run_id,    measurement.run_id)
