"""Проверки математики графика отдельно от Tkinter."""

import unittest

from plotting import quadratic_points


class PlottingTests(unittest.TestCase):
    """Количество точек, границы и неверные коэффициенты."""

    def test_square_function(self):
        x_values, y_values = quadratic_points(1, 0, 0, count=3)

        self.assertEqual(x_values, [-5, 0, 5])
        self.assertEqual(y_values, [25, 0, 25])

    def test_arbitrary_coefficients(self):
        x_values, y_values = quadratic_points(2, -3, 4, count=3)

        self.assertEqual(x_values, [-5, 0, 5])
        self.assertEqual(y_values, [69, 4, 39])

    def test_default_point_count_and_endpoints(self):
        x_values, y_values = quadratic_points(1, 0, 0)

        self.assertEqual(len(x_values), 201)
        self.assertEqual(len(y_values), 201)
        self.assertAlmostEqual(x_values[0], -5)
        self.assertAlmostEqual(x_values[-1], 5)
        self.assertAlmostEqual(x_values[100], 0)

    def test_linear_and_constant_functions(self):
        self.assertEqual(quadratic_points(0, 2, 1, count=3)[1], [-9, 1, 11])
        self.assertEqual(quadratic_points(0, 0, 3, count=3)[1], [3, 3, 3])

    def test_non_finite_coefficients_are_rejected(self):
        for value in (float("nan"), float("inf"), -float("inf")):
            for coefficients in ((value, 0, 0), (0, value, 0), (0, 0, value)):
                with self.subTest(coefficients=coefficients):
                    with self.assertRaises(ValueError):
                        quadratic_points(*coefficients)

    def test_overflowing_values_are_rejected(self):
        with self.assertRaises(ValueError):
            quadratic_points(1e308, 0, 0)

    def test_invalid_point_count_is_rejected(self):
        for count in (0, 1, -1, 2.5, True):
            with self.subTest(count=count):
                with self.assertRaises(ValueError):
                    quadratic_points(1, 0, 0, count=count)


if __name__ == "__main__":
    unittest.main()
