"""Текстовое поле и обработчик кнопки."""

import tkinter as tk
from tkinter import ttk


class WidgetsTab(ttk.Frame):
    """Основные элементы интерфейса."""

    def __init__(self, master) -> None:
        super().__init__(master, padding=20)
        self.columnconfigure(0, weight=1)
        text_frame = ttk.LabelFrame(self, text="Вывод текста", padding=12)
        text_frame.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        text_frame.columnconfigure(0, weight=1)

        self.text_value = tk.StringVar()
        self.text_entry = ttk.Entry(text_frame, textvariable=self.text_value)
        self.text_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.show_button = ttk.Button(
            text_frame, text="Показать текст", command=self.display_text
        )
        self.show_button.grid(row=0, column=1)
        self.text_entry.bind("<Return>", lambda event: self.display_text())

        self.output_text = tk.StringVar(value="Здесь появится введённый текст.")
        ttk.Label(
            text_frame, textvariable=self.output_text, wraplength=730
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(12, 0))

    def display_text(self) -> None:
        """Показывает введённый текст или сообщение о пустом поле."""
        text = self.text_value.get().strip()
        self.output_text.set(text if text else "Введите текст в поле выше.")
