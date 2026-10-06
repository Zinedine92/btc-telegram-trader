import unittest
from decimal import Decimal

from strategy import Analysis
from risk_gate import evaluate_analysis


class RiskGateTests(unittest.TestCase):
    def good_analysis(self):
        return Analysis(
            bias="LONG", score=75.0,
            entry=Decimal("100000"),
            stop_loss=Decimal("99000"),
            take_profit=Decimal("102000"),
            reason="test",
        )

    def test_valid_setup_passes_gate(self):
        approved, message, result = evaluate_analysis(self.good_analysis(), 1000, 20)
        self.assertTrue(approved)
        self.assertTrue(result.approved)
        self.assertIn("Execution remains disabled", message)

    def test_excessive_leverage_is_blocked(self):
        approved, message, _ = evaluate_analysis(self.good_analysis(), 1000, 50)
        self.assertFalse(approved)
        self.assertIn("RISK BLOCKED", message)

    def test_no_trade_is_blocked(self):
        analysis = Analysis("NO_TRADE", 0.0, Decimal("100000"), Decimal("100000"), Decimal("100000"), "none")
        approved, message, _ = evaluate_analysis(analysis, 1000, 20)
        self.assertFalse(approved)
        self.assertIn("NO_TRADE", message)


if __name__ == "__main__":
    unittest.main()
