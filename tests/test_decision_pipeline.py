"""Tests for the read-only Signal -> Risk decision pipeline."""

import unittest

from decision_pipeline import DecisionPipeline
from validation.signal_validator import Signal


def valid_signal():
    return Signal(
        side="LONG",
        score=85,
        entry_price=100000,
        stop_loss=99000,
        take_profit=102000,
        market_regime="TRENDING",
        structure_confirmed=True,
        setup_confirmed=True,
    )


class DecisionPipelineTests(unittest.TestCase):
    def test_valid_signal_passes_both_gates(self):
        result = DecisionPipeline().evaluate(valid_signal(), equity=1000, leverage=5)
        self.assertTrue(result.approved)
        self.assertEqual(result.stage, "RISK_ENGINE")
        self.assertIsNotNone(result.risk)
        self.assertAlmostEqual(result.risk.risk_amount, 5.0)

    def test_bad_signal_stops_before_risk_engine(self):
        signal = valid_signal()
        signal = Signal(**{**signal.__dict__, "score": 60})
        result = DecisionPipeline().evaluate(signal, equity=1000, leverage=5)
        self.assertFalse(result.approved)
        self.assertEqual(result.stage, "SIGNAL_VALIDATION")

    def test_risk_limit_blocks_after_signal_passes(self):
        result = DecisionPipeline().evaluate(
            valid_signal(), equity=1000, leverage=21
        )
        self.assertFalse(result.approved)
        self.assertEqual(result.stage, "RISK_ENGINE")


if __name__ == "__main__":
    unittest.main()
