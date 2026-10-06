"""Tests for deterministic signal validation."""

import unittest

from signal.signal_validator import Signal, SignalValidator


class SignalValidatorTests(unittest.TestCase):
    def setUp(self):
        self.validator = SignalValidator()

    def valid_signal(self):
        return Signal(
            side="LONG",
            score=80,
            entry_price=100000,
            stop_loss=99000,
            take_profit=102000,
            market_regime="TRENDING",
            structure_confirmed=True,
            setup_confirmed=True,
        )

    def test_valid_signal_passes(self):
        result = self.validator.validate(self.valid_signal())
        self.assertTrue(result.valid)

    def test_low_score_is_blocked(self):
        signal = Signal(**{**self.valid_signal().__dict__, "score": 69})
        result = self.validator.validate(signal)
        self.assertFalse(result.valid)

    def test_unconfirmed_structure_is_blocked(self):
        signal = Signal(**{**self.valid_signal().__dict__, "structure_confirmed": False})
        result = self.validator.validate(signal)
        self.assertFalse(result.valid)

    def test_bad_long_geometry_is_blocked(self):
        signal = Signal(**{**self.valid_signal().__dict__, "stop_loss": 101000})
        result = self.validator.validate(signal)
        self.assertFalse(result.valid)

    def test_bad_short_geometry_is_blocked(self):
        signal = Signal(
            side="SHORT",
            score=80,
            entry_price=100000,
            stop_loss=99000,
            take_profit=98000,
            market_regime="TRENDING",
            structure_confirmed=True,
            setup_confirmed=True,
        )
        result = self.validator.validate(signal)
        self.assertFalse(result.valid)


if __name__ == "__main__":
    unittest.main()
