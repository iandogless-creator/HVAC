from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtGui import QColor, QPalette


@dataclass(frozen=True)
class AppearanceTokensV1:
    window: str
    text: str
    base: str
    alternate_base: str
    button: str
    button_hover: str
    button_pressed: str
    disabled_text: str
    border: str
    dock_title: str
    link: str
    calculate: str
    calculate_hover: str
    add: str
    add_hover: str
    remove: str
    remove_hover: str
    category_main_border: str
    category_main_title: str
    category_helper_border: str
    category_helper_title: str
    panel_focus_fill: str
    panel_focus_border: str
    panel_focus_text: str


_LIGHT = AppearanceTokensV1(
    window="#f3f4f5",
    text="#202326",
    base="#ffffff",
    alternate_base="#edf0f2",
    button="#e4e7e9",
    button_hover="#d8dde0",
    button_pressed="#cbd1d5",
    disabled_text="#8b9298",
    border="#c7ccd0",
    dock_title="#e9ecee",
    link="#2f6f9f",
    calculate="#3f7f5b",
    calculate_hover="#346f4e",
    add="#607f96",
    add_hover="#536f84",
    remove="#985f54",
    remove_hover="#844f46",
    category_main_border="#667f94",
    category_main_title="#dce6ed",
    category_helper_border="#7d70a0",
    category_helper_title="#e8e3f0",
    panel_focus_fill="#f3cf9c",
    panel_focus_border="#a76222",
    panel_focus_text="#202326",
)

_DARK = AppearanceTokensV1(
    window="#202326",
    text="#e2e5e7",
    base="#17191b",
    alternate_base="#25292c",
    button="#30353a",
    button_hover="#3a4045",
    button_pressed="#252a2e",
    disabled_text="#858c92",
    border="#454b50",
    dock_title="#2a2e32",
    link="#75add5",
    calculate="#4d8a63",
    calculate_hover="#5b9a72",
    add="#607f96",
    add_hover="#6d8da4",
    remove="#9d655b",
    remove_hover="#ad7469",
    category_main_border="#7898b3",
    category_main_title="#607f96",
    category_helper_border="#a090bd",
    category_helper_title="#8073a3",
    panel_focus_fill="#e5b36f",
    panel_focus_border="#f0a14a",
    panel_focus_text="#202326",
)


def appearance_tokens_v1(scheme: str) -> AppearanceTokensV1:
    return _DARK if str(scheme or "").strip().lower() == "dark" else _LIGHT


def application_palette_v1(scheme: str) -> QPalette:
    tokens = appearance_tokens_v1(scheme)
    palette = QPalette()
    roles = {
        QPalette.ColorRole.Window: tokens.window,
        QPalette.ColorRole.WindowText: tokens.text,
        QPalette.ColorRole.Base: tokens.base,
        QPalette.ColorRole.AlternateBase: tokens.alternate_base,
        QPalette.ColorRole.ToolTipBase: tokens.base,
        QPalette.ColorRole.ToolTipText: tokens.text,
        QPalette.ColorRole.Text: tokens.text,
        QPalette.ColorRole.Button: tokens.button,
        QPalette.ColorRole.ButtonText: tokens.text,
        QPalette.ColorRole.BrightText: "#ffffff",
        QPalette.ColorRole.Link: tokens.link,
        QPalette.ColorRole.Highlight: tokens.panel_focus_fill,
        QPalette.ColorRole.HighlightedText: tokens.panel_focus_text,
        QPalette.ColorRole.PlaceholderText: tokens.disabled_text,
    }
    for role, colour in roles.items():
        palette.setColor(role, QColor(colour))
    for role in (
        QPalette.ColorRole.WindowText,
        QPalette.ColorRole.Text,
        QPalette.ColorRole.ButtonText,
    ):
        palette.setColor(
            QPalette.ColorGroup.Disabled,
            role,
            QColor(tokens.disabled_text),
        )
    return palette


def application_stylesheet_v1(scheme: str) -> str:
    tokens = appearance_tokens_v1(scheme)
    return f"""
    QDockWidget {{
        border: 1px solid {tokens.border};
    }}
    QDockWidget::title {{
        background: {tokens.dock_title};
        border-bottom: 1px solid {tokens.border};
        padding: 4px 6px;
    }}
    QDockWidget[hvacPanelCategory="main_readonly"] {{
        border: 2px solid {tokens.category_main_border};
    }}
    QDockWidget[hvacPanelCategory="main_readonly"]::title {{
        background: {tokens.category_main_title};
        color: {tokens.text};
        border-bottom: 2px solid {tokens.category_main_border};
    }}
    QDockWidget[hvacPanelCategory="helper_input"] {{
        border: 2px solid {tokens.category_helper_border};
    }}
    QDockWidget[hvacPanelCategory="helper_input"]::title {{
        background: {tokens.category_helper_title};
        color: {tokens.text};
        border-bottom: 2px solid {tokens.category_helper_border};
    }}
    QDockWidget[hvacPanelFocus="active"] {{
        border: 3px solid {tokens.panel_focus_border};
    }}
    QDockWidget[hvacPanelFocus="active"]::title {{
        background: {tokens.panel_focus_fill};
        color: {tokens.panel_focus_text};
        border-bottom: 3px solid {tokens.panel_focus_border};
    }}
    QPushButton {{
        background: {tokens.button};
        color: {tokens.text};
        border: 1px solid {tokens.border};
        border-radius: 3px;
        min-height: 22px;
        padding: 3px 10px;
    }}
    QPushButton:hover {{
        background: {tokens.button_hover};
    }}
    QPushButton:pressed {{
        background: {tokens.button_pressed};
    }}
    QPushButton:disabled {{
        color: {tokens.disabled_text};
    }}
    QPushButton[hvacAction="calculate"] {{
        background: {tokens.calculate};
        color: #ffffff;
        border-color: {tokens.calculate};
        font-weight: 600;
    }}
    QPushButton[hvacAction="calculate"]:hover {{
        background: {tokens.calculate_hover};
    }}
    QPushButton[hvacAction="add"] {{
        background: {tokens.add};
        color: #ffffff;
        border-color: {tokens.add};
    }}
    QPushButton[hvacAction="add"]:hover {{
        background: {tokens.add_hover};
    }}
    QPushButton[hvacAction="remove"] {{
        background: {tokens.remove};
        color: #ffffff;
        border-color: {tokens.remove};
    }}
    QPushButton[hvacAction="remove"]:hover {{
        background: {tokens.remove_hover};
    }}
    QPushButton[hvacAction="calculate"]:disabled,
    QPushButton[hvacAction="add"]:disabled,
    QPushButton[hvacAction="remove"]:disabled {{
        background: {tokens.button};
        color: {tokens.disabled_text};
        border-color: {tokens.border};
    }}
    QTableWidget::item:selected,
    QListWidget::item:selected,
    QTreeWidget::item:selected,
    QComboBox QAbstractItemView::item:selected,
    QTableWidget::item:selected:active,
    QListWidget::item:selected:active,
    QTreeWidget::item:selected:active,
    QComboBox QAbstractItemView::item:selected:active,
    QTableWidget::item:selected:!active,
    QListWidget::item:selected:!active,
    QTreeWidget::item:selected:!active,
    QComboBox QAbstractItemView::item:selected:!active {{
        background: {tokens.panel_focus_fill};
        color: {tokens.panel_focus_text};
    }}
    """.strip()
