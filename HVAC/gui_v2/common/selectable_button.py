from PySide6.QtWidgets import QPushButton


class SelectableButton(QPushButton):
    """
    Standard selectable button for GUI v2.

    Visual rules:
    - Thin blue outline by default
    - Thick blue outline when selected
    """

    def __init__(self, text: str):
        super().__init__(text)
        self.setCheckable(True)

    def set_selected(self, selected: bool) -> None:
        self.blockSignals(True)
        self.setChecked(selected)
        self.blockSignals(False)
