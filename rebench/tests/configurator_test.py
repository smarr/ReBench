import unittest
import os
import logging

from rebench.configurator           import Configurator
from rebench.persistence            import DataPointPersistence
from rebench.model.benchmark_config import BenchmarkConfig
from rebench.model.run_id           import RunId

class ConfiguratorTest(unittest.TestCase):
    
    def setUp(self):
        BenchmarkConfig.reset()
        RunId.reset()
        DataPointPersistence.reset()
        self._path = os.path.dirname(os.path.realpath(__file__))
        self._logging_error = logging.error
    
    def tearDown(self):
        logging.error = self._logging_error  # restore normal logging
        
    def test_experiment_name_from_cli(self):
        cnf = Configurator(self._path + '/test.conf', None, 'TestBrokenCommandFormat')
        
        self.assertEqual('TestBrokenCommandFormat', cnf.experiment_name())
    
    def test_experiment_name_from_config_file(self):
        cnf = Configurator(self._path + '/test.conf', None)
        self.assertEqual('Test', cnf.experiment_name())
        
    def test_number_of_experiments_smallconf(self):
        cnf = Configurator(self._path + '/small.conf', None)
        self.assertEqual(1, len(cnf.get_experiments()))

    def test_number_of_experiments_testconf(self):
        cnf = Configurator(self._path + '/test.conf', None, 'all')
        self.assertEqual(6, len(cnf.get_experiments()))
        
    def test_get_experiment(self):
        cnf = Configurator(self._path + '/small.conf', None)
        exp = cnf.get_experiment('Test')
        self.assertIsNotNone(exp)
        return exp

    def test_get_runs(self):
        exp = self.test_get_experiment()
        runs = exp.get_runs()
        self.assertEqual(2 * 2 * 2, len(runs))

# allow command-line execution 
def test_suite():
    return unittest.makeSuite(ConfiguratorTest)

if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')