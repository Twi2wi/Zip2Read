from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt6.QtCore import Qt

class InfoPage(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 32, 32, 32)
        lay.setSpacing(16)

        title = QLabel("О ПРИЛОЖЕНИИ")
        title.setObjectName("section_title")
        lay.addWidget(title)

        c1 = QFrame()
        c1.setObjectName("card")
        cl1 = QVBoxLayout(c1)
        cl1.setSpacing(8)
        cl1.addWidget(QLabel("Zip2Read").setObjectName("card_title") and self._style_lbl(c1, "font-size: 16px; letter-spacing: 1px; background: transparent;"))
        cl1.addWidget(self._make_lbl("Инструмент для извлечения исходного кода из ZIP-архивов с генерацией структурированного Markdown-дампа. Поддерживает интерактивные якоря, раздельные карты файлов и статистику по языкам.", None))
        lay.addWidget(c1)

        c2 = QFrame()
        c2.setObjectName("card")
        cl2 = QVBoxLayout(c2)
        cl2.setSpacing(6)
        cl2.addWidget(self._make_lbl("КАК ЭТО РАБОТАЕТ", "section_title"))
        for t in ["1. Выберите конфигурацию расширений.", "2. Перетащите .zip архив или выберите файл.", "3. Нажмите «Извлечь в Markdown».", "4. Дамп сохранится в Documents/Zip2Read.", "5. Откройте файл в любом Markdown-редакторе."]:
            cl2.addWidget(self._make_lbl(t, None))
        lay.addWidget(c2)

        c3 = QFrame()
        c3.setObjectName("card")
        cl3 = QVBoxLayout(c3)
        cl3.setSpacing(6)
        cl3.addWidget(self._make_lbl("ОСОБЕННОСТИ", "section_title"))
        for t in ["• Интерактивные якоря в дереве файлов", "• Раздельные карты кода и бинарных файлов", "• Статистика по языкам с процентным соотношением", "• Игнорирование битых файлов и защита от крахов", "• Гибкая система пресетов расширений (JSON)"]:
            cl3.addWidget(self._make_lbl(t, None))
        lay.addWidget(c3)

        lay.addStretch()

    def _make_lbl(self, text: str, obj_name: str | None) -> QLabel:
        lbl = QLabel(text)
        if obj_name: lbl.setObjectName(obj_name)
        else: lbl.setStyleSheet("color: #2C2430; font-size: 12px; padding: 2px 0; line-height: 1.4; background: transparent;")
        lbl.setWordWrap(True)
        return lbl