# Файл: themes.py
def get_style(theme: str) -> str:
    if theme == "dark":
        p = {
            "bg": "#1F1B24",
            "text": "#EDE7F2",
            "sidebar": "#2A2433",
            "sidebar_border": "#3D344A",
            "logo": "#B39DDB",
            "muted": "#9B8AAE",
            "nav_text": "#C5B8D6",
            "accent": "#FF9E43",
            "accent_hover": "#FFB74D",
            "accent_dark": "#F28C33",
            "accent_soft": "rgba(255, 158, 67, 0.10)",
            "accent_softer": "rgba(255, 158, 67, 0.16)",
            "card": "#26202E",
            "card_border": "#3D344A",
            "input_bg": "#2E2838",
            "input_border": "#4A3F5A",
            "selected": "#4A3B63",
            "good": "#81C784",
            "bad": "#E57373",
            "warn": "#FFB74D",
            "bad_soft": "rgba(229, 115, 115, 0.12)",
            "scroll_bg": "#1F1B24",
            "scroll_handle": "#4A3F5A"
        }
    else:
        p = {
            "bg": "#F8F6F2",
            "text": "#2C2430",
            "sidebar": "#EDE5F5",
            "sidebar_border": "#D8C8E8",
            "logo": "#7A5C9A",
            "muted": "#9B8AAE",
            "nav_text": "#6B5A7E",
            "accent": "#FF9E43",
            "accent_hover": "#FFB74D",
            "accent_dark": "#F28C33",
            "accent_soft": "rgba(255, 158, 67, 0.08)",
            "accent_softer": "rgba(255, 158, 67, 0.12)",
            "card": "#FDFCF9",
            "card_border": "#E8DFF0",
            "input_bg": "#FFFFFF",
            "input_border": "#D8C8E8",
            "selected": "#E6D8FF",
            "good": "#2E7D32",
            "bad": "#C62828",
            "warn": "#F57C00",
            "bad_soft": "rgba(198, 40, 40, 0.08)",
            "scroll_bg": "#F8F6F2",
            "scroll_handle": "#D8C8E8"
        }

    style = """
QMainWindow, QWidget { background-color: @bg@; color: @text@; font-family: 'Segoe UI', 'Consolas', sans-serif; }
QFrame { background: transparent; }
QLabel, QCheckBox { background: transparent; }
QPushButton:focus { outline: none; }

#sidebar { background-color: @sidebar@; border-right: 1px solid @sidebar_border@; min-width: 220px; max-width: 220px; }
#logo_label { color: @logo@; font-size: 20px; font-weight: bold; letter-spacing: 3px; padding: 20px 16px 8px 16px; background: transparent; }
#version_label { color: @muted@; font-size: 10px; padding: 0 16px 20px 16px; letter-spacing: 1px; background: transparent; }
#separator { background: @sidebar_border@; max-height: 1px; border: none; }

#nav_btn { background: transparent; border: none; color: @nav_text@; font-size: 12px; letter-spacing: 1px; text-align: left; padding: 12px 20px; border-left: 2px solid transparent; }
#nav_btn:hover { color: @accent@; background: @accent_soft@; border-left: 2px solid @accent@; }
#nav_btn[active="true"] { color: @accent@; background: @accent_softer@; border-left: 2px solid @accent@; }

#card, QFrame#card { background: @card@; border: 1px solid @card_border@; border-radius: 12px; padding: 12px; }
#card_title { color: @logo@; font-size: 11px; letter-spacing: 2px; background: transparent; }
#section_title { background: transparent; color: @logo@; font-size: 11px; letter-spacing: 3px; padding: 0 0 8px 0; }
#muted_label { color: @muted@; font-size: 11px; background: transparent; }

#add_btn { background: transparent; border: 1px dashed @input_border@; border-radius: 8px; color: @logo@; font-size: 12px; padding: 8px 10px; letter-spacing: 1px; }
#add_btn:hover { border-color: @accent@; color: @accent@; background: @accent_soft@; }
#add_btn:disabled { color: @muted@; border-color: @card_border@; }

#danger_btn { background: transparent; border: 1px dashed @bad@; border-radius: 8px; color: @bad@; font-size: 12px; padding: 8px 10px; }
#danger_btn:hover { background: @bad_soft@; }

#connect_btn { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 @accent@, stop:1 @accent_dark@); border: none; border-radius: 8px; color: #FFFFFF; font-size: 13px; font-weight: bold; letter-spacing: 1px; padding: 10px 14px; }
#connect_btn:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 @accent_hover@, stop:1 @accent@); }
#connect_btn:disabled { background: @card_border@; color: @muted@; }

#settings_container { background: transparent; }

QLineEdit, QSpinBox, QComboBox, QPlainTextEdit { background: @input_bg@; border: 1px solid @input_border@; border-radius: 6px; padding: 7px; color: @text@; }
QLineEdit:focus, QSpinBox:focus, QComboBox:focus, QPlainTextEdit:focus { border-color: @accent@; outline: none; }

QComboBox::drop-down { border: none; width: 22px; }
QComboBox::down-arrow { image: none; }
QComboBox QAbstractItemView { background: @input_bg@; color: @text@; border: 1px solid @input_border@; selection-background-color: @selected@; selection-color: @text@; }

QSpinBox::up-button, QSpinBox::down-button { width: 16px; }

QCheckBox { spacing: 8px; }
QCheckBox::indicator { width: 16px; height: 16px; border-radius: 4px; border: 1px solid @input_border@; background: @input_bg@; }
QCheckBox::indicator:checked { background: @accent@; border-color: @accent@; }

QProgressBar { border: 1px solid @input_border@; border-radius: 6px; background: @bg@; height: 14px; text-align: center; color: transparent; }
QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 @accent@, stop:1 @accent_dark@); border-radius: 5px; }

QScrollBar:vertical { background: @scroll_bg@; width: 8px; border-radius: 4px; }
QScrollBar::handle:vertical { background: @scroll_handle@; border-radius: 4px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

QScrollBar:horizontal { background: @scroll_bg@; height: 8px; border-radius: 4px; }
QScrollBar::handle:horizontal { background: @scroll_handle@; border-radius: 4px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

QScrollArea { background: transparent; border: none; }

 QTreeWidget, QListWidget, QTableWidget { background: @input_bg@; border: 1px solid @input_border@; border-radius: 6px; padding: 2px; color: @text@; }
 QTreeWidget::item, QListWidget::item, QTableWidget::item { padding: 3px 4px; }
 QTreeWidget::item:selected, QListWidget::item:selected, QTableWidget::item:selected { background: @selected@; color: @text@; }
 QTreeWidget::item:hover, QListWidget::item:hover { background: @accent_soft@; }
 QHeaderView::section { background: @sidebar@; color: @nav_text@; border: none; border-right: 1px solid @input_border@; border-bottom: 1px solid @input_border@; padding: 5px 6px; }
 QTableCornerButton::section { background: @sidebar@; border: none; }
 QTabWidget::pane { border: 1px solid @card_border@; border-radius: 8px; top: -1px; }
 QTabBar::tab { background: transparent; color: @nav_text@; padding: 8px 14px; font-size: 12px; border: 1px solid transparent; border-top-left-radius: 6px; border-top-right-radius: 6px; }
 QTabBar::tab:selected { color: @accent@; background: @accent_softer@; border-color: @card_border@; }
 QTabBar::tab:hover { color: @accent@; }
 QSplitter::handle { background: @card_border@; }
 QSplitter::handle:horizontal { width: 2px; }
 QSplitter::handle:vertical { height: 2px; }

 #drop_zone { border: 2px dashed @input_border@; border-radius: 12px; background: @card@; color: @muted@; padding: 12px; }
 #drop_zone[drop="true"] { border-color: @accent@; background: @accent_soft@; color: @accent@; }
"""

    for key, value in p.items():
        style = style.replace(f"@{key}@", value)

    return style