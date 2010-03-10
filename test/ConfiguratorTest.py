import unittest

from Configurator import Configurator

class ConfiguratorTest(unittest.TestCase):
        
    def test_loadAndAccessors(self):        
        cnf = Configurator('test/test.conf', None)
        
        self.assertEqual(dict, type(cnf.quick_runs))
        self.assertEqual(dict, type(cnf.benchmark_suites))
        
    def test_runNameFromCli(self):
        cnf = Configurator('test/test.conf', None, 'fooTest')
        
        self.assertEqual('fooTest', cnf.runName())
    
    def test_runNameFromConfigFile(self):
        cnf = Configurator('test/test.conf', None)
        self.assertEqual('Test', cnf.runName())
        
    def test_getRunDefinitions(self):
        cnf = Configurator('test/test.conf', None)
        self.assert_(cnf.getRunDefinitions())


# allow commandline execution 
def test_suite():
    return unittest.makeSuite(ConfiguratorTest)

if __name__ == "__main__":
    unittest.main(defaultTest='test_suite')