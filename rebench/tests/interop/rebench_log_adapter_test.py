from unittest import TestCase

from ...interop.rebench_log_adapter import RebenchLogAdapter


class RebenchAdapterTest(TestCase):

    def _assert_basics(self, data, val, unit, criterion, total):
        self.assertEqual(1, len(data))
        point = data[0]
        self.assertEqual(val, point.get_total_value())

        self.assertEqual(1, len(point.get_measurements()))
        measure = point.get_measurements()[0]

        self.assertEqual(total, measure.is_total())
        self.assertEqual(val, measure.value)
        self.assertEqual(criterion, measure.criterion)
        self.assertEqual(unit, measure.unit)

    def _assert_two_measures(self, data, val1, unit1, criterion1, val_t, unit_t):
        self.assertEqual(1, len(data))
        point = data[0]
        self.assertEqual(val_t, point.get_total_value())

        self.assertEqual(2, len(point.get_measurements()))
        measure = point.get_measurements()[0]

        self.assertFalse(measure.is_total())
        self.assertEqual(val1, measure.value)
        self.assertEqual(criterion1, measure.criterion)
        self.assertEqual(unit1, measure.unit)

        measure = point.get_measurements()[1]
        self.assertTrue(measure.is_total())
        self.assertEqual(val_t, measure.value)
        self.assertEqual(unit_t, measure.unit)

    def test_simple_name(self):
        adapter = RebenchLogAdapter(True)
        data = adapter.parse_data("Dispatch: iterations=1 runtime: 557ms", None, 1)
        self._assert_basics(data, 557, 'ms', 'total', True)

    def test_doted_name(self):
        adapter = RebenchLogAdapter(True)
        data = adapter.parse_data(
            "LanguageFeatures.Dispatch: iterations=1 runtime: 309557us", None, 1)
        self._assert_basics(data, 309.557, 'ms', 'total', True)

    def test_doted_and_ms(self):
        adapter = RebenchLogAdapter(True)
        data = adapter.parse_data(
            "LanguageFeatures.Dispatch: iterations=1 runtime: 557ms", None, 1)
        self._assert_basics(data, 557, 'ms', 'total', True)

    def test_high_iter_count(self):
        adapter = RebenchLogAdapter(True)
        data = adapter.parse_data(
            "LanguageFeatures.Dispatch: iterations=2342 runtime: 557ms", None, 1)
        self._assert_basics(data, 557, 'ms', 'total', True)

    def test_total_explicit(self):
        adapter = RebenchLogAdapter(True)
        data = adapter.parse_data(
            "LanguageFeatures.Dispatch total: iterations=2342 runtime: 557ms",
            None, 1)
        self._assert_basics(data, 557, 'ms', 'total', True)

    def test_alloc_criterion(self):
        adapter = RebenchLogAdapter(True)
        data = adapter.parse_data(
            """LanguageFeatures.Dispatch alloc: iterations=2342 runtime: 222ms
LanguageFeatures.Dispatch total: iterations=2342 runtime: 557ms""",
            None, 3)
        self._assert_two_measures(data, 222, 'ms', 'alloc', 557, 'ms')

    def test_foobar_criterion(self):
        adapter = RebenchLogAdapter(True)
        data = adapter.parse_data(
            """LanguageFeatures.Dispatch foobar: iterations=2342 runtime: 550ms
LanguageFeatures.Dispatch total: iterations=2342 runtime: 557ms""",
            None, 5)
        self._assert_two_measures(data, 550, 'ms', 'foobar', 557, 'ms')

    def test_foobar_criterion_no_doted_name(self):
        adapter = RebenchLogAdapter(True)
        data = adapter.parse_data(
            """Dispatch foobar: iterations=2342 runtime: 550ms
LanguageFeatures.Dispatch total: iterations=2342 runtime: 557ms""",
            None, 7)
        self._assert_two_measures(data, 550, 'ms', 'foobar', 557, 'ms')

    def test_some_prefix_before_data(self):
        adapter = RebenchLogAdapter(True)
        data = adapter.parse_data(
            "some prefix: Dispatch: iterations=2342 runtime: 557ms",
            None, 11)
        self._assert_basics(data, 557, 'ms', 'total', True)

    def test_path_as_name(self):
        adapter = RebenchLogAdapter(True)
        data = adapter.parse_data(
            "core-lib/Benchmarks/Join/FibSeq.ns: iterations=1 runtime: 129us",
            None, 12)
        self._assert_basics(data, 0.129, 'ms', 'total', True)

    def test_other_data(self):
        adapter = RebenchLogAdapter(True)
        data = adapter.parse_data("""Savina.Chameneos: trace size:    3903398byte
Savina.Chameneos: external data: 40byte
Savina.Chameneos: iterations=1 runtime: 64208us
Savina.Chameneos: trace size:    3903414byte
Savina.Chameneos: external data: 40byte
Savina.Chameneos: iterations=1 runtime: 48581us""", None, 13)

        self.assertEqual(2, len(data))
        point = data[0]
        self.assertEqual(64.208, point.get_total_value())

        self.assertEqual(3, len(point.get_measurements()))
        measure = point.get_measurements()[0]

        self.assertFalse(measure.is_total())
        self.assertEqual(3903398, measure.value)
        self.assertEqual('trace size', measure.criterion)
        self.assertEqual('byte', measure.unit)

        measure = point.get_measurements()[1]
        self.assertFalse(measure.is_total())
        self.assertEqual(40, measure.value)
        self.assertEqual('external data', measure.criterion)
        self.assertEqual('byte', measure.unit)
