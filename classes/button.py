from PyQt6.QtWidgets import QPushButton
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize, pyqtProperty


class Button(QPushButton):
    def __init__(self, text="", icon_path=None, variant="primary",
                 icon_size=24, parent=None):
        super().__init__(text, parent)

        self.variant = variant
        self._order = 0
        self._row = 0
        self._col = 0
        # Used by QSS to style buttons differently via [variant="..."]
        self.setProperty("variant", variant)

        if icon_path:
            icon = QIcon(icon_path)
            self.setIcon(QIcon(icon_path))
            self.setIconSize(QSize(icon_size, icon_size))
            print(f"Icon path: {icon_path} | isNull: {icon.isNull()}")

    def set_variant(self, variant: str):
        """Change style at runtime (e.g. 'primary' -> 'danger')."""
        self.variant = variant
        self.setProperty("variant", variant)
        # Force Qt to re-apply the stylesheet after a dynamic property change
        self.style().unpolish(self)
        self.style().polish(self)
    def get_order(self):
        return self._order

    def set_order(self, value):
        self._order = value

    order = pyqtProperty(int, get_order, set_order)

    def get_row(self):
        return self._row

    def set_row(self, value):
        self._row = value

    row = pyqtProperty(int, get_row, set_row)

    def get_col(self):
        return self._col

    def set_col(self, value):
        self._col = value

    col = pyqtProperty(int, get_col, set_col) 