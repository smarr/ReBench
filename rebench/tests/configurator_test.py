import unittest
import os
import logging

from ..Configurator import Configurator
from ..model.benchmark_config import BenchmarkConfig
from ..model.runs_config import RunsConfig, QuickRunsConfig

class ConfiguratorTest(unittest.TestCase):
    
    def setUp(self):
        BenchmarkConfig.reset()
        self._path = os.path.dirname(os.path.realpath(__file__))
        self._logging_error = logging.error
    
    def tearDown(self):
        logging.error = self._logging_error  # restore normal logging
        
    def test_structure(self):        
        cnf = Configurator(self._path + '/test.conf', None)
                
        self.assertIsInstance(cnf.runs,             RunsConfig)
        self.assertIsInstance(cnf.quick_runs,       QuickRunsConfig)
        self.assertIsInstance(cnf.benchmark_suites, dict)
        
    def test_experiment_name_from_cli(self):
        cnf = Configurator(self._path + '/test.conf', None, 'TestBrokenCommandFormat')
        
        self.assertEqual('TestBrokenCommandFormat', cnf.experiment_name())
    
    def test_experiment_name_from_config_file(self):
        cnf = Configurator(self._path + '/test.conf', None)
        self.assertEqual('Test', cnf.experiment_name())
        
    def test_get_benchmark_configurations(self):
        cnf = Configurator(self._path + '/test.conf', None)
        self.assertIsNotNone(cnf.getBenchmarkConfigurations())

    def test_warning_for_removed_ulimit(self):
        def test_logging(msg, *args, **kwargs):
            self.assertIn('ulimit', args, "Test that ulimit is recognized as unsupported")
            raise RuntimeError("TEST-PASSED")
        
        logging.error = test_logging
        
        with self.assertRaisesRegexp(RuntimeError, "TEST-PASSED"):
            Configurator(self._path + '/test.conf', None, 'TestWarningForRemovedUlimitUsage')
        


# allow command-line execution 
def test_suite():
    return unittest.makeSuite(ConfiguratorTest)

if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')