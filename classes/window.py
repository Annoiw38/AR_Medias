from classes.button import Button
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My Window")
        self.setGeometry(100, 100, 400, 300)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Dictionary to gest widget with names or keys
        self._widgets = {}

    # Add a widget
    def add_widget(self, key: str, widget: QWidget, index: int = None):
        if key in self._widgets:
            raise ValueError(f"Widget con chiave '{key}' esiste già")

        self._widgets[key] = widget

        if index is None:
            self.layout.addWidget(widget)
        else:
            self.layout.insertWidget(index, widget)

    # Remove a widget
    def remove_widget(self, key: str):
        widget = self._widgets.pop(key, None)
        if widget is None:
            return

        self.layout.removeWidget(widget)
        widget.setParent(None)   # stacca il widget dalla finestra
        widget.deleteLater()     # lo elimina dalla memoria

    # Get a widget to modify
    def get_widget(self, key: str) -> QWidget:
        return self._widgets.get(key)

    # Hide or show without delete
    def toggle_widget(self, key: str, visible: bool = None):
        widget = self._widgets.get(key)
        if widget is None:
            return
        widget.setVisible(not widget.isVisible() if visible is None else visible)

    # Replace a widget
    def replace_widget(self, key: str, new_widget: QWidget):
        old_widget = self._widgets.get(key)
        if old_widget is None:
            self.add_widget(key, new_widget)
            return

        index = self.layout.indexOf(old_widget)
        self.remove_widget(key)
        self.add_widget(key, new_widget, index=index)
    def set_grid_layout(self, grid_layout, widgets: dict):
        """Sostituisce il layout principale con una griglia e registra i widget."""
        if self.layout is not None:
            QWidget().setLayout(self.layout)

        self.layout = grid_layout
        self.setLayout(self.layout)
        self._widgets.update(widgets)