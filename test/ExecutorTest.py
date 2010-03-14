import unittest
import subprocess

from Executor import Executor
from rebench  import ReBench

class ExecutorTest(unittest.TestCase):
        
    def test_benchmark(self):        
        # construct test config
        config = { 'statistics':
                    {'min_runs': 30,
                     'max_runs': 50,
                     'confidence_level': 0.95,
                     'error_margin': 0.005},
                   'virtual_machines': { 'test-vm': {
                                                     'path' : None,
                                                     'binary' : None
                                                     }
                                        },
                   'benchmarks': {'test': {
                                     'performance_reader' : 'TestPerformance',
                                     'command' : '',
                                     'input_sizes': [1],
                                     'benchmarks': ['test-bench'],
                                     'ulimit': None }},
                    'options' : {'use_nice': False}
        }
        executions = ['test-vm']
        
        # before executing the benchmark, we override stuff in subprocess for testing
        subprocess.Popen =  Popen_override
        
        ex = Executor(config, "", "benchmark", executions, "test", 1)
        ex.execute()
        
        (mean, sdev, (interval, interval_percentage), 
                (interval_t, interval_percentage_t)) = ex.result['test-vm']['test-bench']
        
        self.assertEqual(31, len(ex.benchmark_data['test-vm']['test-bench']))
        self.assertAlmostEqual(45870.4193548, mean)
        self.assertAlmostEqual(2.93778711485, sdev)
        
        (i_low, i_high) = interval
        self.assertAlmostEqual(45869.385195243565, i_low)
        self.assertAlmostEqual(45871.453514433859, i_high)
        self.assertAlmostEqual(0.00450904792104, interval_percentage)

def Popen_override(cmdline, stdout, shell):
    class Popen:
        returncode = 0
        def communicate(self):
            return (None, None)
    
    return Popen()

def test_suite():
    return unittest.makeSuite(ExecutorTest)

if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')