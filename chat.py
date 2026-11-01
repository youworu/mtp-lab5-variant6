"""Локальный TCP-чат: сервер, клиенты и очередь входящих сообщений."""

import json
import queue
import socket
import socketserver
import threading


HOST = "127.0.0.1"
MAX_LINE = 8192


def validate_name(name: str) -> str:
    """Проверяет имя участника и убирает внешние пробелы."""
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 30:
        raise ValueError("Имя должно содержать от 1 до 30 символов")
    if "\n" in name or "\r" in name:
        raise ValueError("Имя должно занимать одну строку")
    return name.strip()


def validate_text(text: str) -> str:
    """Проверяет непустое сообщение длиной до 1000 символов."""
    if not isinstance(text, str) or not 1 <= len(text.strip()) <= 1000:
        raise ValueError("Сообщение должно содержать от 1 до 1000 символов")
    return text.strip()


def _decode_message(line: str) -> tuple[str, str]:
    if len(line) > MAX_LINE:
        raise ValueError("Слишком длинное сообщение")
    payload = json.loads(line)
    if not isinstance(payload, dict):
        raise ValueError("Ожидался объект сообщения")
    return validate_name(payload.get("name")), validate_text(payload.get("text"))


def _encode_message(name: str, text: str) -> bytes:
    payload = {"name": validate_name(name), "text": validate_text(text)}
    return (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")


def _close_socket(connection: socket.socket) -> None:
    try:
        connection.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass
    connection.close()


class _ChatHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        if not self.server.attach(self.request):
            return
        try:
            with self.request.makefile("r", encoding="utf-8") as source:
                while line := source.readline(MAX_LINE + 1):
                    name, text = _decode_message(line)
                    self.server.broadcast(_encode_message(name, text))
        except (OSError, ValueError, UnicodeError):
            return
        finally:
            self.server.detach(self.request)


class _LocalServer(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, port: int) -> None:
        self.clients = set()
        self.clients_lock = threading.Lock()
        self.send_lock = threading.Lock()
        self.stopping = threading.Event()
        super().__init__((HOST, port), _ChatHandler)

    def attach(self, connection: socket.socket) -> bool:
        with self.send_lock:
            with self.clients_lock:
                if self.stopping.is_set():
                    return False
                self.clients.add(connection)
            try:
                connection.sendall(b'{"type":"ready"}\n')
            except OSError:
                self.detach(connection)
                return False
        return True

    def detach(self, connection: socket.socket) -> None:
        with self.clients_lock:
            self.clients.discard(connection)

    def broadcast(self, data: bytes) -> None:
        with self.send_lock:
            with self.clients_lock:
                recipients = list(self.clients)
            for connection in recipients:
                try:
                    connection.sendall(data)
                except OSError:
                    self.detach(connection)
                    _close_socket(connection)


class ChatServer:
    """Рассылает сообщения всем подключённым локальным участникам."""

    def __init__(self, port: int = 8765) -> None:
        self.port = port
        self._server = None
        self._thread = None

    def start(self) -> None:
        """Открывает порт и запускает сервер в отдельном потоке."""
        if self._server is not None:
            raise RuntimeError("Сервер уже запущен")
        self._server = _LocalServer(self.port)
        self.port = self._server.server_address[1]
        self._thread = threading.Thread(
            target=self._server.serve_forever,
            kwargs={"poll_interval": 0.1},
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        """Прекращает приём подключений и закрывает клиентские сокеты."""
        server = self._server
        if server is None:
            return
        server.stopping.set()
        server.shutdown()
        with server.clients_lock:
            connections = list(server.clients)
        for connection in connections:
            _close_socket(connection)
        server.server_close()
        self._thread.join(timeout=2)
        self._server = None
        self._thread = None


class ChatClient:
    """Получает сообщения в очередь, не обращаясь к виджетам Tkinter."""

    def __init__(self, name: str) -> None:
        self.name = validate_name(name)
        self.messages = queue.Queue()
        self._socket = None
        self._thread = None
        self._connected = threading.Event()
        self._ready = threading.Event()

    @property
    def connected(self) -> bool:
        return self._connected.is_set()

    def connect(self, port: int = 8765) -> None:
        """Подключается к серверу и ждёт подтверждения готовности."""
        self.close()
        self._ready.clear()
        connection = socket.create_connection((HOST, port), timeout=2)
        connection.settimeout(None)
        self._socket = connection
        self._connected.set()
        self._thread = threading.Thread(
            target=self._receive, args=(connection,), daemon=True
        )
        self._thread.start()
        if not self._ready.wait(timeout=2) or not self.connected:
            self.close()
            raise ConnectionError("Сервер не подтвердил подключение")

    def _receive(self, connection: socket.socket) -> None:
        try:
            with connection.makefile("r", encoding="utf-8") as source:
                while line := source.readline(MAX_LINE + 1):
                    if json.loads(line) == {"type": "ready"}:
                        self._ready.set()
                    else:
                        self.messages.put(_decode_message(line))
        except (OSError, ValueError, UnicodeError):
            return
        finally:
            self._connected.clear()
            connection.close()

    def send(self, text: str) -> None:
        """Отправляет сообщение; отображение происходит после рассылки сервера."""
        if not self.connected:
            raise ConnectionError("Сначала подключитесь к чату")
        self._socket.sendall(_encode_message(self.name, text))

    def close(self) -> None:
        """Закрывает сокет и завершает поток чтения."""
        self._connected.clear()
        connection, self._socket = self._socket, None
        if connection is not None:
            _close_socket(connection)
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None
