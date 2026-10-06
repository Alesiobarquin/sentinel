"""Prevent failed/healthy controls or repeated packets from inflating claims."""

from pathlib import Path
import unittest

from scripts.summarize_resume_evaluation import study_summary


REPORT = Path(__file__).resolve().parents[1] / "evals/reports/resume-20261005"


class StudySummaryTests(unittest.TestCase):
    def test_control_followup_stays_out_of_fault_accuracy(self):
        result = study_summary(REPORT)
        self.assertEqual(result["primary_fault_accuracy"]["denominator"], 27)
        self.assertEqual(result["primary_control_abstention"]["denominator"], 18)
        self.assertEqual(result["evaluated_attempts"], 63)
        self.assertEqual(result["total_sprint_attempts"], 67)

    def test_reusing_a_cohort_cannot_inflate_the_study(self):
        with self.assertRaisesRegex(ValueError, "Repeated run ID"):
            study_summary(REPORT, cohorts=(".", "."))
