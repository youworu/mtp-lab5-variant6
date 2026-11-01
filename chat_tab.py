"""Вкладка локального чата с получением сообщений через очередь."""

import queue
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

from chat import ChatClient, ChatServer


class ChatTab(ttk.Frame):
    """Позволяет создать чат или подключиться из другого экземпляра."""

    def __init__(self, master, name: str, port: int) -> None:
        super().__init__(master, padding=16)
        self.port = port
        self.client = None
        self.server = None
        self._poll_job = None

        controls = ttk.Frame(self)
        controls.pack(fill="x", pady=(0, 12))
        ttk.Label(controls, text="Имя:").pack(side="left", padx=(0, 6))
        self.name_value = tk.StringVar(value=name)
        self.name_entry = ttk.Entry(controls, textvariable=self.name_value, width=18)
        self.name_entry.pack(side="left", padx=(0, 12))
        ttk.Label(controls, text=f"127.0.0.1:{port}").pack(side="left", padx=(0, 12))
        self.host_button = ttk.Button(
            controls, text="Создать чат", command=self.host_chat
        )
        self.host_button.pack(side="left", padx=(0, 8))
        self.connect_button = ttk.Button(
            controls, text="Подключиться", command=self.connect_chat
        )
        self.connect_button.pack(side="left", padx=(0, 8))
        self.disconnect_button = ttk.Button(
            controls, text="Отключиться", command=self.disconnect_chat
        )
        self.disconnect_button.pack(side="left")

        self.status = tk.StringVar(value="Создайте чат или подключитесь к запущенному.")
        ttk.Label(self, textvariable=self.status, wraplength=800).pack(
            anchor="w", pady=(0, 10)
        )
        self.history = ScrolledText(self, height=15, wrap="word", state="disabled")
        self.history.pack(fill="both", expand=True)
        composer = ttk.Frame(self)
        composer.pack(fill="x", pady=(12, 0))
        self.message_value = tk.StringVar()
        self.message_entry = ttk.Entry(composer, textvariable=self.message_value)
        self.message_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.message_entry.bind("<Return>", lambda event: self.send_message())
        self.send_button = ttk.Button(
            composer, text="Отправить", command=self.send_message
        )
        self.send_button.pack(side="left")
        self.stop_button = ttk.Button(
            self, text="Остановить свой сервер", command=self.stop_server
        )
        self.stop_button.pack(anchor="w", pady=(12, 0))
        self._refresh_controls()
        self._poll_job = self.after(100, self._poll_messages)

    def _refresh_controls(self) -> None:
        connected = self.client is not None and self.client.connected
        for widget in (self.name_entry, self.connect_button):
            widget.state(["disabled"] if connected else ["!disabled"])
        self.host_button.state(
            ["disabled"] if connected or self.server is not None else ["!disabled"]
        )
        for widget in (self.disconnect_button, self.message_entry, self.send_button):
            widget.state(["!disabled"] if connected else ["disabled"])
        self.stop_button.state(["!disabled"] if self.server else ["disabled"])

    def host_chat(self) -> None:
        """Запускает локальный сервер и подключает владельца."""
        try:
            client = ChatClient(self.name_value.get())
            server = ChatServer(self.port)
            server.start()
        except (OSError, ValueError, RuntimeError) as error:
            self.status.set(f"Не удалось создать чат: {error}")
            return
        self.server = server
        self._connect_client(client)

    def connect_chat(self) -> None:
        """Подключает участника к ранее созданному чату."""
        try:
            client = ChatClient(self.name_value.get())
        except ValueError as error:
            self.status.set(str(error))
            return
        self._connect_client(client)

    def _connect_client(self, client: ChatClient) -> None:
        if self.client is not None:
            self.client.close()
        try:
            client.connect(self.port)
        except OSError as error:
            client.close()
            self.client = None
            self.status.set(f"Нет соединения. Сначала создайте чат. {error}")
        else:
            self.client = client
            self.status.set(f"Подключено: {client.name} · 127.0.0.1:{self.port}")
            self.message_entry.focus_set()
        self._refresh_controls()

    def disconnect_chat(self) -> None:
        """Закрывает только соединение текущего участника."""
        if self.client is not None:
            self.client.close()
            self.client = None
        self.status.set("Отключено. Можно подключиться снова.")
        self._refresh_controls()

    def stop_server(self) -> None:
        """Останавливает сервер, созданный этим экземпляром приложения."""
        self.disconnect_chat()
        if self.server is not None:
            self.server.stop()
            self.server = None
        self.status.set("Сервер остановлен.")
        self._refresh_controls()

    def send_message(self) -> None:
        """Отправляет текст; собственное сообщение также приходит с сервера."""
        if self.client is None:
            self.status.set("Сначала подключитесь к чату.")
            return
        try:
            self.client.send(self.message_value.get())
        except (OSError, ValueError) as error:
            self.status.set(str(error))
        else:
            self.message_value.set("")

    def _poll_messages(self) -> None:
        """Переносит сообщения из очереди в виджет в главном потоке Tkinter."""
        if self.client is not None:
            while True:
                try:
                    name, text = self.client.messages.get_nowait()
                except queue.Empty:
                    break
                self.history.configure(state="normal")
                self.history.insert("end", f"{name}: {text}\n")
                self.history.configure(state="disabled")
                self.history.see("end")
            if not self.client.connected:
                self.client.close()
                self.client = None
                self.status.set("Соединение закрыто сервером.")
                self._refresh_controls()
        self._poll_job = self.after(100, self._poll_messages)

    def close(self) -> None:
        """Отменяет опрос очереди и освобождает сетевые ресурсы."""
        if self._poll_job is not None:
            self.after_cancel(self._poll_job)
            self._poll_job = None
        self.stop_server()
