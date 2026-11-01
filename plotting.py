"""Расчёт точек квадратичной функции без графического интерфейса."""

import math


def quadratic_points(
    a: float, b: float, c: float, *, count: int = 201
) -> tuple[list[float], list[float]]:
    """Возвращает count точек y = ax² + bx + c на отрезке [-5, 5]."""
    if not all(math.isfinite(value) for value in (a, b, c)):
        raise ValueError("Коэффициенты должны быть конечными числами")
    if type(count) is not int or count < 2:
        raise ValueError("Количество точек должно быть целым числом не меньше 2")
    x_values = [-5 + 10 * index / (count - 1) for index in range(count)]
    y_values = [a * x * x + b * x + c for x in x_values]
    if not all(math.isfinite(value) for value in y_values):
        raise ValueError("Слишком большие значения коэффициентов")
    return x_values, y_values
