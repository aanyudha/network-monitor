from __future__ import annotations


def build_stylesheet(mode: str = "dark") -> str:
    if mode == "light":
        surface = "#f5f7fb"
        panel = "#ffffff"
        panel_alt = "#eef2f9"
        text = "#132238"
        muted = "#5d6b80"
        border = "#d5ddeb"
    else:
        surface = "#0c121c"
        panel = "#162231"
        panel_alt = "#1d2c3f"
        text = "#edf4ff"
        muted = "#9db2cb"
        border = "#2d4057"

    return f"""
    QWidget {{
        background-color: {surface};
        color: {text};
        font-family: 'Segoe UI', 'Noto Sans', sans-serif;
        font-size: 10pt;
    }}
    QMainWindow {{
        background-color: {surface};
    }}
    QFrame#sidebar {{
        background-color: {panel};
        border-right: 1px solid {border};
    }}
    QFrame#panel, QFrame#card {{
        background-color: {panel};
        border: 1px solid {border};
        border-radius: 16px;
    }}
    QFrame#panelAlt {{
        background-color: {panel_alt};
        border: 1px solid {border};
        border-radius: 16px;
    }}
    QPushButton {{
        background-color: {panel_alt};
        border: 1px solid {border};
        border-radius: 10px;
        padding: 8px 14px;
    }}
    QPushButton:hover {{
        border-color: #4ca3ff;
    }}
    QPushButton[accent="true"] {{
        background-color: #1f7ae0;
        color: white;
        border-color: #1f7ae0;
    }}
    QLineEdit, QComboBox, QSpinBox, QTableWidget, QListWidget, QTextEdit {{
        background-color: {panel};
        border: 1px solid {border};
        border-radius: 10px;
        padding: 6px;
    }}
    QHeaderView::section {{
        background-color: {panel_alt};
        border: none;
        padding: 8px;
    }}
    QProgressBar {{
        background-color: {panel_alt};
        border: 1px solid {border};
        border-radius: 8px;
        text-align: center;
    }}
    QProgressBar::chunk {{
        background-color: #33c27f;
        border-radius: 7px;
    }}
    QLabel[muted="true"] {{
        color: {muted};
    }}
    QLabel[badge="online"] {{
        background-color: #1d6f4f;
        color: white;
        border-radius: 10px;
        padding: 4px 8px;
    }}
    QLabel[badge="offline"] {{
        background-color: #8d2d39;
        color: white;
        border-radius: 10px;
        padding: 4px 8px;
    }}
    QLabel[badge="warning"] {{
        background-color: #8a6218;
        color: white;
        border-radius: 10px;
        padding: 4px 8px;
    }}
    QLabel[badge="unknown"] {{
        background-color: #495a73;
        color: white;
        border-radius: 10px;
        padding: 4px 8px;
    }}
    """

