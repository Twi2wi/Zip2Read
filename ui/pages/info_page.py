# ui
from PyQt6.QtWidgets import QFrame, QLabel, QScrollArea, QVBoxLayout, QWidget

from utils.version import __app_name__, __version__


class InfoPage(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 20, 28, 20)
        outer.setSpacing(8)
        title = QLabel("О ПРИЛОЖЕНИИ")
        title.setObjectName("section_title")
        outer.addWidget(title)
        sep = QFrame()
        sep.setObjectName("separator")
        outer.addWidget(sep)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        container = QWidget()
        container.setObjectName("settings_container")
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        self._add_card(lay, f"{__app_name__.upper()} {__version__}", [
            "Извлечение исходников из ZIP-архивов в дамп для чтения глазами или для скармливания ИИ.",
            "Два формата, выборочная экстракция, поиск по содержимому, инструменты для готовых Markdown-дампов."
        ])
        self._add_card(lay, "ФОРМАТЫ ДАМПА", [
            "MD — человекочитаемый: заголовки, статистика, карта кода с якорями, содержимое в code-блоках.",
            "TXT — экономный: только пути и содержимое, разделители ---, без разметки и ссылок. Заметно меньше токенов.",
            "В обоих форматах всегда есть полный список файлов архива и блок выбранных с ключами отбора.",
            "Эмодзи вычищаются из дампа полностью, включая содержимое файлов."
        ])
        self._add_card(lay, "ВЫБОРКА", [
            "Весь архив — всё, кроме исключений из настроек.",
            "Папка — отметьте папки в дереве, вложенные файлы попадают автоматически.",
            "Файлы — отметьте нужные, есть фильтр по имени и выбор всех видимых.",
            "По содержимому — текст или regex, в дамп идут только файлы с совпадением.",
            "Ключи отбора: search: запрос, file: путь, folder: путь. Файл входит в тело один раз."
        ])
        self._add_card(lay, "ИНСТРУМЕНТЫ MARKDOWN", [
            "Поиск по загруженным дампам: текст или regex, подсветка совпадения в контексте, выгрузка всех результатов.",
            "Статистика: строки, слова, символы, код-блоки, заголовки, ссылки, изображения — с учётом code-блоков.",
            "Извлечение элементов и объединение файлов с предпросмотром и отдельным сохранением.",
            "Все операции идут в фоне, их можно отменить."
        ])
        self._add_card(lay, "ОСОБЕННОСТИ", [
            "Потоковая запись: память не забивается содержимым всего архива.",
            "Отмена срабатывает даже внутри чтения большого файла.",
            "Пресеты расширений, исключения, лимит размера, fallback-кодировка.",
            "Светлая и тёмная тема, прогресс по текущему файлу.",
            "Кэш предпросмотра с инвалидацией по времени изменения файла."
        ])
        lay.addStretch()
        scroll.setWidget(container)
        outer.addWidget(scroll, 1)

    def _add_card(self, parent_lay: QVBoxLayout, title: str, lines: list[str]):
        card = QFrame()
        card.setObjectName("card")
        card_lay = QVBoxLayout(card)
        card_lay.setSpacing(6)
        t = QLabel(title)
        t.setObjectName("card_title")
        card_lay.addWidget(t)
        for text in lines:
            lbl = QLabel(text)
            lbl.setObjectName("muted_label")
            lbl.setWordWrap(True)
            card_lay.addWidget(lbl)
        parent_lay.addWidget(card)