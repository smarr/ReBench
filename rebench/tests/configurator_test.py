import unittest
import os

from ..Configurator import Configurator, BenchmarkConfig

class ConfiguratorTest(unittest.TestCase):
    
    def setUp(self):
        BenchmarkConfig.reset()
        self._path = os.path.dirname(os.path.realpath(__file__))
        
    def test_loadAndAccessors(self):        
        cnf = Configurator(self._path + '/test.conf', None)
                
        self.assertIsInstance(cnf.quick_runs,       dict)
        self.assertIsInstance(cnf.benchmark_suites, dict)
        
    def test_runNameFromCli(self):
        cnf = Configurator(self._path + '/test.conf', None, 'Test')
        
        self.assertEqual('Test', cnf.runName())
    
    def test_runNameFromConfigFile(self):
        cnf = Configurator(self._path + '/test.conf', None)
        self.assertEqual('Test', cnf.runName())
        
    def test_getBenchmarkConfigurations(self):
        cnf = Configurator(self._path + '/test.conf', None)
        self.assertIsNotNone(cnf.getBenchmarkConfigurations())


# allow commandline execution 
def test_suite():
    return unittest.makeSuite(ConfiguratorTest)

if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')