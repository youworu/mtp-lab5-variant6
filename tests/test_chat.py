"""Проверки настоящего TCP-обмена через loopback-интерфейс."""

import socket
import time
import unittest

from chat import ChatClient, ChatServer, validate_name, validate_text


class ValidationTests(unittest.TestCase):
    """Пустые значения, ограничения длины и кириллица."""

    def test_valid_name_and_message(self):
        self.assertEqual(validate_name("  Дарья  "), "Дарья")
        self.assertEqual(validate_text("  Привет!  "), "Привет!")

    def test_invalid_names(self):
        for name in ("", "   ", "a" * 31, "первая\nвторая", None):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    validate_name(name)

    def test_invalid_messages(self):
        for text in ("", "   ", "a" * 1001, None):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    validate_text(text)


class ChatTests(unittest.TestCase):
    """Несколько клиентов, отключение и некорректные пакеты."""

    def setUp(self):
        self.server = ChatServer(port=0)
        self.server.start()
        self.addCleanup(self.server.stop)

    def connect(self, name):
        client = ChatClient(name)
        self.addCleanup(client.close)
        client.connect(self.server.port)
        self.assertTrue(client.connected)
        return client

    def test_two_clients_receive_the_same_message(self):
        first = self.connect("Дарья")
        second = self.connect("Собеседник")
        first.send("Привет, мир!")

        expected = ("Дарья", "Привет, мир!")
        self.assertEqual(first.messages.get(timeout=2), expected)
        self.assertEqual(second.messages.get(timeout=2), expected)

    def test_messages_are_sent_in_both_directions(self):
        first = self.connect("Первый")
        second = self.connect("Второй")
        first.send("Первое")
        second.send("Второе")

        first_received = {first.messages.get(timeout=2) for _ in range(2)}
        second_received = {second.messages.get(timeout=2) for _ in range(2)}
        expected = {("Первый", "Первое"), ("Второй", "Второе")}
        self.assertEqual(first_received, expected)
        self.assertEqual(second_received, expected)

    def test_unicode_newlines_and_json_characters(self):
        client = self.connect("Дарья")
        text = 'Текст с "кавычками"\nи новой строкой: 😀'
        client.send(text)

        self.assertEqual(client.messages.get(timeout=2), ("Дарья", text))

    def test_empty_message_does_not_break_the_connection(self):
        client = self.connect("Дарья")
        with self.assertRaises(ValueError):
            client.send("   ")
        client.send("После ошибки")

        self.assertEqual(client.messages.get(timeout=2), ("Дарья", "После ошибки"))

    def test_one_client_can_leave_without_stopping_the_chat(self):
        first = self.connect("Первый")
        second = self.connect("Второй")
        first.close()
        second.send("Связь работает")

        self.assertEqual(second.messages.get(timeout=2), ("Второй", "Связь работает"))

    def test_malformed_packet_disconnects_only_its_sender(self):
        client = self.connect("Дарья")
        with socket.create_connection(
            ("127.0.0.1", self.server.port), timeout=2
        ) as raw:
            raw.settimeout(2)
            ready = raw.recv(1024)
            self.assertIn(b"ready", ready)
            raw.sendall(b"not json\n")
            self.assertEqual(raw.recv(1024), b"")
        client.send("После неверного пакета")

        self.assertEqual(
            client.messages.get(timeout=2), ("Дарья", "После неверного пакета")
        )

    def test_stopping_server_disconnects_clients(self):
        client = self.connect("Дарья")
        self.server.stop()
        deadline = time.monotonic() + 2
        while client.connected and time.monotonic() < deadline:
            time.sleep(0.01)

        self.assertFalse(client.connected)

    def test_send_without_connection_is_rejected(self):
        client = ChatClient("Дарья")
        with self.assertRaises(ConnectionError):
            client.send("Привет")

    def test_repeated_start_is_rejected_and_stop_is_idempotent(self):
        with self.assertRaises(RuntimeError):
            self.server.start()
        self.server.stop()
        self.server.stop()


if __name__ == "__main__":
    unittest.main()
