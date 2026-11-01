"""Текстовое поле, прогрессбар и выбор файла."""

import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk


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

        progress_frame = ttk.LabelFrame(self, text="Прогресс", padding=12)
        progress_frame.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        progress_frame.columnconfigure(0, weight=1)
        self.progress_value = tk.IntVar(value=0)
        self.progress = ttk.Progressbar(
            progress_frame, maximum=100, variable=self.progress_value
        )
        self.progress.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        self.progress_text = tk.StringVar(value="0%")
        ttk.Label(progress_frame, textvariable=self.progress_text, width=6).grid(
            row=0, column=1
        )
        controls = ttk.Frame(progress_frame)
        controls.grid(row=1, column=0, columnspan=2, sticky="w", pady=(12, 0))
        self.start_button = ttk.Button(
            controls, text="Запустить", command=self.start_progress
        )
        self.start_button.pack(side="left", padx=(0, 8))
        ttk.Button(controls, text="Пауза", command=self.pause_progress).pack(
            side="left", padx=(0, 8)
        )
        ttk.Button(controls, text="Сбросить", command=self.reset_progress).pack(
            side="left"
        )
        self._progress_job = None

        file_frame = ttk.LabelFrame(self, text="Выбор файла", padding=12)
        file_frame.grid(row=2, column=0, sticky="ew")
        self.file_button = ttk.Button(
            file_frame, text="Выбрать файл…", command=self.choose_file
        )
        self.file_button.pack(anchor="w")
        self.selected_file = tk.StringVar(value="Файл не выбран.")
        ttk.Label(
            file_frame, textvariable=self.selected_file, wraplength=730
        ).pack(anchor="w", pady=(12, 0))

    def display_text(self) -> None:
        """Показывает введённый текст или сообщение о пустом поле."""
        text = self.text_value.get().strip()
        self.output_text.set(text if text else "Введите текст в поле выше.")

    def start_progress(self) -> None:
        """Запускает обновление без блокировки цикла событий."""
        if self._progress_job is not None:
            return
        if self.progress_value.get() == 100:
            self.progress_value.set(0)
        self.start_button.state(["disabled"])
        self._advance_progress()

    def _advance_progress(self) -> None:
        value = min(100, self.progress_value.get() + 2)
        self.progress_value.set(value)
        self.progress_text.set(f"{value}%")
        self._progress_job = None
        if value < 100:
            self._progress_job = self.after(80, self._advance_progress)
        else:
            self.start_button.state(["!disabled"])

    def pause_progress(self) -> None:
        """Останавливает обновление, сохраняя текущее значение."""
        if self._progress_job is not None:
            self.after_cancel(self._progress_job)
            self._progress_job = None
        self.start_button.state(["!disabled"])

    def reset_progress(self) -> None:
        """Останавливает прогрессбар и возвращает его в начало."""
        self.pause_progress()
        self.progress_value.set(0)
        self.progress_text.set("0%")

    def close(self) -> None:
        """Отменяет отложенный вызов перед закрытием окна."""
        self.pause_progress()

    def choose_file(self) -> None:
        """Открывает системный диалог и показывает выбранный путь."""
        filename = filedialog.askopenfilename(
            parent=self,
            title="Выберите файл",
            initialdir=Path(__file__).resolve().parent / "examples",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")],
        )
        if filename:
            self.selected_file.set(filename)
