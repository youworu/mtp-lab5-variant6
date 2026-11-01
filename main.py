"""Запуск приложения Tkinter."""

import argparse

from app import Application


def main() -> None:
    """Разбирает имя участника и порт локального чата."""
    parser = argparse.ArgumentParser(description="Лабораторная №5, вариант 6")
    parser.add_argument("--name", default="Дарья", help="Имя участника чата")
    parser.add_argument("--port", type=int, default=8765, help="Порт локального чата")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("Порт должен быть от 1 до 65535")
    application = Application(args.name, args.port)
    application.mainloop()


if __name__ == "__main__":
    main()
