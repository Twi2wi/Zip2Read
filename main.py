# Файл: main.py
import sys

from PyQt6.QtWidgets import QApplication

from core.settings import load_settings
from themes import get_style
from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    settings = load_settings()
    app.setStyleSheet(get_style(settings.theme))

    win = MainWindow(settings)
    win.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()