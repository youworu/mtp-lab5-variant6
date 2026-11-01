"""График matplotlib, встроенный в виджет Tkinter."""

import tkinter as tk
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from plotting import quadratic_points


class PlotTab(ttk.Frame):
    """Строит y = ax² + bx + c с коэффициентами из полей ввода."""

    def __init__(self, master) -> None:
        super().__init__(master, padding=16)
        controls = ttk.Frame(self)
        controls.pack(fill="x", pady=(0, 12))
        self.coefficients = []
        for label, default in (("a", "1"), ("b", "0"), ("c", "0")):
            ttk.Label(controls, text=f"{label} =").pack(side="left", padx=(0, 5))
            value = tk.StringVar(value=default)
            ttk.Entry(controls, textvariable=value, width=9).pack(
                side="left", padx=(0, 16)
            )
            self.coefficients.append(value)
        self.plot_button = ttk.Button(
            controls, text="Построить", command=self.draw_plot
        )
        self.plot_button.pack(side="left")
        self.plot_status = tk.StringVar()
        ttk.Label(self, textvariable=self.plot_status, foreground="#a12424").pack(
            anchor="w", pady=(0, 6)
        )

        self.figure = Figure(figsize=(7, 4.5), dpi=100, layout="constrained")
        self.axes = self.figure.add_subplot()
        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        self.draw_plot()

    def draw_plot(self) -> None:
        """Обновляет встроенный график или показывает ошибку ввода."""
        try:
            a, b, c = (
                float(value.get().strip().replace(",", "."))
                for value in self.coefficients
            )
            x_values, y_values = quadratic_points(a, b, c)
        except (ValueError, OverflowError) as error:
            self.plot_status.set(f"Проверьте коэффициенты: {error}")
            return

        self.axes.clear()
        self.axes.plot(x_values, y_values, color="#2458a6", linewidth=2)
        self.axes.axhline(0, color="gray", linewidth=0.7)
        self.axes.axvline(0, color="gray", linewidth=0.7)
        self.axes.set_title(f"y = {a:g}x² {b:+g}x {c:+g}")
        self.axes.set_xlabel("x")
        self.axes.set_ylabel("y")
        self.axes.grid(True, alpha=0.3)
        self.plot_status.set("")
        self.canvas.draw_idle()
