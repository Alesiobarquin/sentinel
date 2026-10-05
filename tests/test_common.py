import unittest

from sentinel.tools.common import TimeWindow, validate_service


class BoundsTests(unittest.TestCase):
    def test_time_window_has_explicit_units_and_utc_boundaries(self):
        window = TimeWindow(0, 21_600)
        self.assertEqual(window.iso_start, "1970-01-01T00:00:00+00:00")
        self.assertEqual(window.iso_end, "1970-01-01T06:00:00+00:00")

    def test_invalid_or_unbounded_windows_are_rejected(self):
        for start, end in [(0, 0), (60, 0), (-1, 60), (0, 21_601), (True, 60), (0, float("inf")), (float("nan"), 60), (0, "60"), (10**15, 10**15 + 60)]:
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                TimeWindow(start, end)

    def test_service_names_preserve_identity_and_reject_controls(self):
        validate_service("payment-service")
        for value in ["", "  ", "x" * 129, "payment\n", None]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_service(value)
