"""Проверки настоящих виджетов; включаются через RUN_GUI_TESTS=1."""

import os
import socket
import time
import tkinter as tk
import unittest
from unittest.mock import patch


@unittest.skipUnless(os.environ.get("RUN_GUI_TESTS") == "1", "Нужен RUN_GUI_TESTS=1")
class GuiTests(unittest.TestCase):
    """Обработчики Tkinter, встроенный график и обмен через вкладку чата."""

    def setUp(self):
        from app import Application

        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        self.application = Application("Дарья", port)
        self.application.withdraw()
        self.application.update_idletasks()
        self.addCleanup(self.application.close)

    def wait_until(self, predicate, timeout=3):
        deadline = time.monotonic() + timeout
        while not predicate():
            self.application.update()
            if time.monotonic() >= deadline:
                self.fail("Состояние интерфейса не изменилось за отведённое время")
            time.sleep(0.01)

    def test_text_button_displays_entered_text(self):
        tab = self.application.widgets_tab
        tab.text_value.set("Привет, мир!")
        tab.show_button.invoke()

        self.assertEqual(tab.output_text.get(), "Привет, мир!")

    def test_empty_text_is_reported(self):
        tab = self.application.widgets_tab
        tab.text_value.set("   ")
        tab.show_button.invoke()

        self.assertIn("Введите текст", tab.output_text.get())

    def test_progress_advances_through_event_loop_and_can_be_paused(self):
        tab = self.application.widgets_tab
        tab.start_button.invoke()
        initial_value = tab.progress_value.get()
        self.wait_until(lambda: tab.progress_value.get() > initial_value)
        tab.pause_progress()
        paused_value = tab.progress_value.get()

        self.assertIsNone(tab._progress_job)
        self.assertGreater(paused_value, 0)
        self.assertNotIn("disabled", tab.start_button.state())

    def test_progress_cannot_start_a_second_timer(self):
        tab = self.application.widgets_tab
        tab.start_progress()
        job = tab._progress_job
        tab.start_progress()

        self.assertEqual(tab._progress_job, job)

    def test_reset_stops_progress_and_returns_to_zero(self):
        tab = self.application.widgets_tab
        tab.start_progress()
        tab.reset_progress()

        self.assertEqual(tab.progress_value.get(), 0)
        self.assertEqual(tab.progress_text.get(), "0%")
        self.assertIsNone(tab._progress_job)

    def test_progress_finishes_at_one_hundred(self):
        tab = self.application.widgets_tab
        tab.progress_value.set(98)
        tab.start_progress()

        self.assertEqual(tab.progress_value.get(), 100)
        self.assertIsNone(tab._progress_job)
        self.assertNotIn("disabled", tab.start_button.state())

    def test_selected_file_path_is_displayed(self):
        tab = self.application.widgets_tab
        with patch("widgets_tab.filedialog.askopenfilename", return_value="sample.txt"):
            tab.file_button.invoke()

        self.assertEqual(tab.selected_file.get(), "sample.txt")

    def test_cancelled_dialog_preserves_previous_selection(self):
        tab = self.application.widgets_tab
        tab.selected_file.set("previous.txt")
        with patch("widgets_tab.filedialog.askopenfilename", return_value=""):
            tab.choose_file()

        self.assertEqual(tab.selected_file.get(), "previous.txt")

    def test_plot_is_embedded_in_tkinter(self):
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        tab = self.application.plot_tab

        self.assertIsInstance(tab.canvas, FigureCanvasTkAgg)
        self.assertIsInstance(tab.canvas.get_tk_widget(), tk.Canvas)
        self.assertEqual(len(tab.axes.lines[0].get_xdata()), 201)

    def test_plot_rebuilds_with_new_coefficients(self):
        tab = self.application.plot_tab
        for variable, value in zip(tab.coefficients, ("0", "0", "3,5")):
            variable.set(value)
        tab.plot_button.invoke()

        self.assertEqual(tab.plot_status.get(), "")
        self.assertTrue(all(value == 3.5 for value in tab.axes.lines[0].get_ydata()))

    def test_invalid_coefficient_keeps_previous_plot(self):
        tab = self.application.plot_tab
        previous = list(tab.axes.lines[0].get_ydata())
        tab.coefficients[0].set("NaN")
        tab.draw_plot()

        self.assertIn("Проверьте коэффициенты", tab.plot_status.get())
        self.assertEqual(list(tab.axes.lines[0].get_ydata()), previous)

    def test_chat_widgets_exchange_messages_with_another_client(self):
        from chat import ChatClient

        tab = self.application.chat_tab
        tab.host_button.invoke()
        self.assertIsNotNone(tab.client)
        self.assertTrue(tab.client.connected)
        peer = ChatClient("Собеседник")
        self.addCleanup(peer.close)
        peer.connect(tab.port)

        tab.message_value.set("Из окна")
        tab.send_button.invoke()
        self.assertEqual(peer.messages.get(timeout=2), ("Дарья", "Из окна"))
        peer.send("Ответ в окно")
        self.wait_until(lambda: "Ответ в окно" in tab.history.get("1.0", "end"))

        self.assertIn("Дарья: Из окна", tab.history.get("1.0", "end"))
        self.assertIn("Собеседник: Ответ в окно", tab.history.get("1.0", "end"))
        self.assertEqual(tab.message_value.get(), "")

    def test_chat_rejects_an_empty_message_without_disconnect(self):
        tab = self.application.chat_tab
        tab.host_chat()
        tab.message_value.set("   ")
        tab.send_message()

        self.assertIn("Сообщение должно содержать", tab.status.get())
        self.assertTrue(tab.client.connected)

    def test_successful_send_clears_previous_input_error(self):
        tab = self.application.chat_tab
        tab.host_chat()
        tab.send_message()
        self.assertIn("Сообщение должно содержать", tab.status.get())
        tab.message_value.set("Исправленный текст")
        tab.send_message()

        self.assertIn("Подключено:", tab.status.get())
        self.wait_until(lambda: "Исправленный текст" in tab.history.get("1.0", "end"))

    def test_connection_without_server_reports_error_and_keeps_controls_enabled(self):
        tab = self.application.chat_tab
        tab.connect_button.invoke()

        self.assertIsNone(tab.client)
        self.assertIn("Нет соединения", tab.status.get())
        self.assertNotIn("disabled", tab.connect_button.state())

    def test_invalid_name_does_not_start_server(self):
        tab = self.application.chat_tab
        tab.name_value.set("   ")
        tab.host_chat()

        self.assertIsNone(tab.server)
        self.assertIsNone(tab.client)
        self.assertIn("Имя должно содержать", tab.status.get())

    def test_stopping_chat_restores_connection_controls(self):
        tab = self.application.chat_tab
        tab.host_chat()
        tab.stop_server()

        self.assertIsNone(tab.server)
        self.assertIsNone(tab.client)
        self.assertNotIn("disabled", tab.host_button.state())
        self.assertIn("disabled", tab.send_button.state())

    def test_closing_with_pending_progress_and_plot_draw_is_safe(self):
        self.application.widgets_tab.start_progress()
        self.application.plot_tab.draw_plot()
        self.application.close()
        self.application.close()

        self.assertIsNone(self.application.widgets_tab._progress_job)
        self.assertIsNone(self.application.chat_tab._poll_job)


if __name__ == "__main__":
    unittest.main()
