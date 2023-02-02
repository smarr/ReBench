from unittest import TestCase
from ...interop.adapter import instantiate_adapter


class AdapterTest(TestCase):
    def test_load_all_known_adapters(self):
        self.assertIsNotNone(instantiate_adapter("JMH", False, None))
        self.assertIsNotNone(instantiate_adapter("Multivariate", False, None))
        self.assertIsNotNone(instantiate_adapter("Perf", False, None))
        self.assertIsNotNone(instantiate_adapter("PlainSecondsLog", False, None))
        self.assertIsNotNone(instantiate_adapter("RebenchLog", False, None))
        self.assertIsNotNone(instantiate_adapter("SavinaLog", False, None))
        self.assertIsNotNone(instantiate_adapter("Test", False, None))
        self.assertIsNotNone(instantiate_adapter("TestExecutor", False, None))
        self.assertIsNotNone(instantiate_adapter("Time", False, None))
        self.assertIsNotNone(instantiate_adapter("ValidationLog", False, None))

    def test_case_insensitive_names(self):
        self.assertIsNotNone(instantiate_adapter("RebenchLog", False, None))
        self.assertIsNotNone(instantiate_adapter("ReBenchLog", False, None))
        self.assertIsNotNone(instantiate_adapter("rebenchlog", False, None))
        self.assertIsNotNone(instantiate_adapter("REBENCHLOG", False, None))
