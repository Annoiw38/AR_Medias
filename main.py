import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication,QGridLayout

from classes.window import MainWindow
from classes.button import Button

if __name__ == "__main__":
    app = QApplication(sys.argv)
    BASE_DIR = Path(__file__).resolve().parent
    ICON_DIR = BASE_DIR / "assets" / "media-player-control"
    with open(Path(__file__).parent / "style/styles.qss", "r") as f:
        app.setStyleSheet(f.read())

    window = MainWindow()
    buttons: list = [
        Button(icon_path=str(ICON_DIR /"previous.ico"), variant="primary"),
        Button(icon_path=str(ICON_DIR /"play.ico"), variant="primary"),
        Button(icon_path=str(ICON_DIR /"next.ico"), variant="primary"),
    ]

    i: int = 0

    widgets_dict = {}
    grid = QGridLayout()
    grid.setSpacing(20)
    grid.setContentsMargins(100, 100, 100, 100)
    for button_wg in buttons:
        grid.addWidget(button_wg, button_wg.row, button_wg.col)
        widgets_dict["ui_btn" + str(i)] = button_wg
        i += 1

    window.set_grid_layout(grid, widgets_dict)
    window.show()
    sys.exit(app.exec())