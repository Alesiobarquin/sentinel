from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from scripts import first_investigation as exercise
from sentinel.auth import AuthError


class FirstInvestigationTests(unittest.TestCase):
    def test_missing_authentication_stops_before_fault_injection(self):
        with patch.object(exercise, "model_provider", side_effect=AuthError("Sign-in required")), \
                patch.object(exercise.demo, "inject_fault") as inject, redirect_stderr(StringIO()):
            self.assertEqual(exercise.main(["--preflight-only"]), 1)
        inject.assert_not_called()

    def test_cleanup_failure_still_closes_the_model_transport(self):
        provider = Mock()
        state = Mock()
        state.exists.return_value = True
        with patch.object(exercise, "model_provider", return_value=provider), \
                patch.object(exercise.demo, "STATE", state), \
                patch.object(exercise.demo, "reset_fault", side_effect=OSError("Cleanup write failed")), \
                redirect_stderr(StringIO()):
            with self.assertRaises(OSError):
                exercise.main(["--preflight-only"])
        provider.close.assert_called_once()

    def test_unexpected_agent_failure_still_resets_fault_and_closes_provider(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source"
            flags = source / "src/flagd/demo.flagd.json"
            flags.parent.mkdir(parents=True)
            flags.write_text(json.dumps({"flags": {"paymentFailure": {"defaultVariant": "off"}}}))
            provider = Mock()
            reset = Mock()
            with patch.object(exercise, "ROOT", root), patch.object(exercise.demo, "SOURCE", source), \
                    patch.object(exercise.demo, "STATE", root / "fault.json"), \
                    patch.object(exercise, "model_provider", return_value=provider), \
                    patch.object(exercise, "local_tools"), patch.object(exercise, "pause"), \
                    patch.object(exercise, "capture", return_value={"metrics": {"success": True}}), \
                    patch.object(exercise.demo, "inject_fault") as inject, patch.object(exercise.demo, "reset_fault", reset), \
                    patch.object(exercise, "InvestigationRunner") as runner, redirect_stdout(StringIO()):
                runner.return_value.run.side_effect = RuntimeError("Unexpected fixture failure")
                with self.assertRaises(RuntimeError):
                    exercise.main([])
            self.assertEqual(inject.call_args.args, ("payment-failure",))
            self.assertIn("owner_id", inject.call_args.kwargs)
            reset.assert_called_once()
            provider.close.assert_called_once()
