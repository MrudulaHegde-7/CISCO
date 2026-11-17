import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import calculator


class CalculatorTests(unittest.TestCase):
    def test_add(self):
        self.assertEqual(calculator.add(8, 2), 10)

    def test_add_with_zero_and_negative_numbers(self):
        self.assertEqual(calculator.add(0, -2), -2)

    def test_subtract(self):
        self.assertEqual(calculator.subtract(8, 2), 6)

    def test_subtract_equal_and_negative_numbers(self):
        self.assertEqual(calculator.subtract(5, 5), 0)
        self.assertEqual(calculator.subtract(-3, 2), -5)

    def test_multiply(self):
        self.assertEqual(calculator.multiply(8, 2), 16)

    def test_multiply_by_zero_and_negative_number(self):
        self.assertEqual(calculator.multiply(12, 0), 0)
        self.assertEqual(calculator.multiply(-3, 2), -6)

    def test_divide(self):
        self.assertEqual(calculator.divide(8, 2), 4)

    def test_divide_negative_and_decimal_numbers(self):
        self.assertEqual(calculator.divide(-9, 3), -3)
        self.assertAlmostEqual(calculator.divide(1, 4), 0.25)

    def test_divide_by_zero_raises_error(self):
        for denominator in (0, -0.0):
            with self.subTest(denominator=denominator):
                with self.assertRaisesRegex(ZeroDivisionError, "Cannot divide by zero"):
                    calculator.divide(8, denominator)

    def test_quit_accepts_uppercase_and_whitespace(self):
        output = io.StringIO()
        with patch("builtins.input", side_effect=[" Q "]), redirect_stdout(output):
            calculator.main()
        self.assertIn("Goodbye!", output.getvalue())

    def test_invalid_operation_shows_message(self):
        output = io.StringIO()
        with patch("builtins.input", side_effect=["x", "q"]), redirect_stdout(output):
            calculator.main()
        self.assertIn("Invalid choice", output.getvalue())

    def test_invalid_number_shows_message(self):
        output = io.StringIO()
        with patch("builtins.input", side_effect=["1", "not a number", "q"]), redirect_stdout(output):
            calculator.main()
        self.assertIn("Please enter valid numbers.", output.getvalue())

    def test_cli_prints_result_for_decimal_input(self):
        output = io.StringIO()
        inputs = ["1", "1.5", "2.25", "q"]
        with patch("builtins.input", side_effect=inputs), redirect_stdout(output):
            calculator.main()
        self.assertIn("Add result: 3.75", output.getvalue())

    def test_cli_handles_division_by_zero_and_continues(self):
        output = io.StringIO()
        inputs = ["4", "8", "0", "q"]
        with patch("builtins.input", side_effect=inputs), redirect_stdout(output):
            calculator.main()
        self.assertIn("Cannot divide by zero.", output.getvalue())
        self.assertIn("Goodbye!", output.getvalue())


if __name__ == "__main__":
    unittest.main()
