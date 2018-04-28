from unittest import TestCase

from ...interop.rebench_log_adapter import RebenchLogAdapter


class RebenchAdapterTest(TestCase):

    def _assert_basics(self, data, val, unit, criterion, total):
        self.assertEqual(1, len(data))
        dp = data[0]
        self.assertEqual(val, dp.get_total_value())

        self.assertEqual(1, len(dp.get_measurements()))
        m = dp.get_measurements()[0]

        self.assertEqual(total,     m.is_total())
        self.assertEqual(val,       m.value)
        self.assertEqual(criterion, m.criterion)
        self.assertEqual(unit,      m.unit)

    def _assert_two_measures(self, data, val1, unit1, criterion1, val_t, unit_t):
        self.assertEqual(1, len(data))
        dp = data[0]
        self.assertEqual(val_t, dp.get_total_value())

        self.assertEqual(2, len(dp.get_measurements()))
        m1 = dp.get_measurements()[0]

        self.assertFalse(m1.is_total())
        self.assertEqual(val1,       m1.value)
        self.assertEqual(criterion1, m1.criterion)
        self.assertEqual(unit1,      m1.unit)

        m2 = dp.get_measurements()[1]
        self.assertTrue(m2.is_total())
        self.assertEqual(val_t, m2.value)
        self.assertEqual(unit_t, m2.unit)

    def test_simple_name(self):
        l = RebenchLogAdapter(True)
        d = l.parse_data("Dispatch: iterations=1 runtime: 557ms", None)
        self._assert_basics(d, 557, 'ms', 'total', True)

    def test_doted_name(self):
        l = RebenchLogAdapter(True)
        d = l.parse_data(
            "LanguageFeatures.Dispatch: iterations=1 runtime: 309557us", None)
        self._assert_basics(d, 309.557, 'ms', 'total', True)

    def test_doted_and_ms(self):
        l = RebenchLogAdapter(True)
        d = l.parse_data(
            "LanguageFeatures.Dispatch: iterations=1 runtime: 557ms", None)
        self._assert_basics(d, 557, 'ms', 'total', True)

    def test_high_iter_count(self):
        l = RebenchLogAdapter(True)
        d = l.parse_data(
            "LanguageFeatures.Dispatch: iterations=2342 runtime: 557ms", None)
        self._assert_basics(d, 557, 'ms', 'total', True)

    def test_total_explicit(self):
        l = RebenchLogAdapter(True)
        d = l.parse_data(
            "LanguageFeatures.Dispatch total: iterations=2342 runtime: 557ms",
            None)
        self._assert_basics(d, 557, 'ms', 'total', True)

    def test_alloc_criterion(self):
        l = RebenchLogAdapter(True)
        d = l.parse_data(
            """LanguageFeatures.Dispatch alloc: iterations=2342 runtime: 222ms
LanguageFeatures.Dispatch total: iterations=2342 runtime: 557ms""",
            None)
        self._assert_two_measures(d, 222, 'ms', 'alloc', 557, 'ms')

    def test_foobar_criterion(self):
        l = RebenchLogAdapter(True)
        d = l.parse_data(
            """LanguageFeatures.Dispatch foobar: iterations=2342 runtime: 550ms
LanguageFeatures.Dispatch total: iterations=2342 runtime: 557ms""",
            None)
        self._assert_two_measures(d, 550, 'ms', 'foobar', 557, 'ms')

    def test_foobar_criterion_no_doted_name(self):
        l = RebenchLogAdapter(True)
        d = l.parse_data(
            """Dispatch foobar: iterations=2342 runtime: 550ms
LanguageFeatures.Dispatch total: iterations=2342 runtime: 557ms""",
            None)
        self._assert_two_measures(d, 550, 'ms', 'foobar', 557, 'ms')

    def test_some_prefix_before_data(self):
        l = RebenchLogAdapter(True)
        d = l.parse_data(
            "some prefix: Dispatch: iterations=2342 runtime: 557ms",
            None)
        self._assert_basics(d, 557, 'ms', 'total', True)

    def test_path_as_name(self):
        l = RebenchLogAdapter(True)
        d = l.parse_data(
            "core-lib/Benchmarks/Join/FibSeq.ns: iterations=1 runtime: 129us",
            None)
        self._assert_basics(d, 0.129, 'ms', 'total', True)

    def test_other_data(self):
        l = RebenchLogAdapter(True)
        data = l.parse_data("""Savina.Chameneos: trace size:    3903398byte
Savina.Chameneos: external data: 40byte
Savina.Chameneos: iterations=1 runtime: 64208us
Savina.Chameneos: trace size:    3903414byte
Savina.Chameneos: external data: 40byte
Savina.Chameneos: iterations=1 runtime: 48581us""", None)

        self.assertEqual(2, len(data))
        dp = data[0]
        self.assertEqual(64.208, dp.get_total_value())

        self.assertEqual(3, len(dp.get_measurements()))
        m1 = dp.get_measurements()[0]

        self.assertFalse(m1.is_total())
        self.assertEqual(3903398, m1.value)
        self.assertEqual('trace size', m1.criterion)
        self.assertEqual('byte', m1.unit)

        m2 = dp.get_measurements()[1]
        self.assertFalse(m2.is_total())
        self.assertEqual(40, m2.value)
        self.assertEqual('external data', m2.criterion)
        self.assertEqual('byte', m2.unit)

