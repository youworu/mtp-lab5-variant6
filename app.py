"""Главное окно лабораторной работы."""

import tkinter as tk
from tkinter import ttk

from widgets_tab import WidgetsTab


class Application(tk.Tk):
    """Объединяет задания во вкладках одного окна."""

    def __init__(self, name: str = "Дарья", port: int = 8765) -> None:
        super().__init__()
        self.title(f"Лабораторная №5 — {name}")
        self.geometry("960x680")
        self.minsize(820, 600)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=12)
        self.widgets_tab = WidgetsTab(self.notebook)
        self.notebook.add(self.widgets_tab, text="Основное")
        self.protocol("WM_DELETE_WINDOW", self.close)

    def close(self) -> None:
        """Завершает обработчики вкладок и закрывает окно."""
        self.widgets_tab.close()
        self.destroy()
