"""
Modulo con classi PyQt6 riutilizzabili per costruire finestre a partire
da "container" indipendenti (ognuno con il proprio layout), più supporto
completo a QSS.

Classi:
- LayoutMixin: logica comune per aggiungere widget a un layout
  (V/H/Grid). Usata sia da Container che da QtWindow.
- Container(QWidget): un pannello con il proprio layout, da annidare
  dentro altri container o dentro la finestra principale.
- QtWindow(QMainWindow): la finestra principale, che internamente è
  già un container e supporta add_container() per crearne altri.

Richiede: pip install PyQt6
"""

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QPushButton, QLabel, QLineEdit, QCheckBox, QComboBox,
    QSlider, QTextEdit, QListWidget, QScrollArea
)
from PyQt6.QtGui import QPixmap,QIcon
from PyQt6.QtCore import Qt,QSize


class LayoutMixin:
    """
    Mixin con tutti i metodi 'add_*'. Chi la usa deve avere:
    - self._layout  (QVBoxLayout / QHBoxLayout / QGridLayout)
    - self._widgets (dict)
    - self._grid_row, self._grid_col, self._grid_max_cols (per la griglia)
    """

    def _init_layout(self, layout, max_cols=4, spacing=None, margins=None):
        if layout == "vertical":
            self._layout = QVBoxLayout()
        elif layout == "horizontal":
            self._layout = QHBoxLayout()
        elif layout == "grid":
            self._layout = QGridLayout()
        else:
            raise ValueError("layout deve essere 'vertical', 'horizontal' o 'grid'")

        self._widgets = {}
        self._grid_row = 0
        self._grid_col = 0
        self._grid_max_cols = max_cols

        if spacing is not None:
            self.set_spacing(spacing)
        if margins is not None:
            if isinstance(margins, (int, float)):
                self.set_margins(margins)
            else:
                self.set_margins(*margins)

    def _add_to_layout(self, widget, row=None, col=None, colspan=1, rowspan=1, stretch=0):
        if isinstance(self._layout, QGridLayout):
            if row is None:
                row, col = self._grid_row, self._grid_col
                self._grid_col += colspan
                if self._grid_col >= self._grid_max_cols:
                    self._grid_col = 0
                    self._grid_row += 1
            self._layout.addWidget(widget, row, col, rowspan, colspan)
        else:
            self._layout.addWidget(widget, stretch)

    def add_widget(self, widget, name=None, object_name=None, **kwargs):
        """Aggiunge un QWidget qualsiasi a questo container/finestra."""
        if object_name:
            widget.setObjectName(object_name)
        if name:
            self._widgets[name] = widget
        self._add_to_layout(widget, **kwargs)
        return widget

    # --- scorciatoie ---
    def add_button(self, text, name=None, on_click=None, object_name=None,
               icon_p=None, icon_size=24, **kwargs):
        btn = QPushButton(text)
        if on_click:
            btn.clicked.connect(on_click)
        if icon_p:
            icon = QIcon(icon_p)
            btn.setIcon(icon)
            btn.setIconSize(QSize(icon_size, icon_size))  # <-- istanza, non la classe
            print(f"Icon path: {icon_p} | isNull: {icon.isNull()}")

        return self.add_widget(btn, name=name, object_name=object_name, **kwargs)

    def add_label(self, text, name=None, object_name=None, **kwargs):
        lbl = QLabel(text)
        return self.add_widget(lbl, name=name, object_name=object_name, **kwargs)

    def add_line_edit(self, placeholder="", name=None, object_name=None, **kwargs):
        le = QLineEdit()
        le.setPlaceholderText(placeholder)
        return self.add_widget(le, name=name, object_name=object_name, **kwargs)

    def add_checkbox(self, text, name=None, object_name=None, **kwargs):
        cb = QCheckBox(text)
        return self.add_widget(cb, name=name, object_name=object_name, **kwargs)

    def add_combobox(self, items, name=None, object_name=None, **kwargs):
        combo = QComboBox()
        combo.addItems(items)
        return self.add_widget(combo, name=name, object_name=object_name, **kwargs)

    def add_slider(self, minimum=0, maximum=100, orientation="horizontal",
                   name=None, object_name=None, **kwargs):
        orient = Qt.Orientation.Horizontal if orientation == "horizontal" else Qt.Orientation.Vertical
        slider = QSlider(orient)
        slider.setMinimum(minimum)
        slider.setMaximum(maximum)
        return self.add_widget(slider, name=name, object_name=object_name, **kwargs)

    def add_text_edit(self, text="", name=None, object_name=None, **kwargs):
        te = QTextEdit()
        te.setPlainText(text)
        return self.add_widget(te, name=name, object_name=object_name, **kwargs)

    def add_list_widget(self, items=None, name=None, object_name=None, **kwargs):
        lw = QListWidget()
        if items:
            lw.addItems(items)
        return self.add_widget(lw, name=name, object_name=object_name, **kwargs)

    def add_image(self, path=None, data=None, width=None, height=None, keep_aspect=True,
                  name=None, object_name=None, **kwargs):
        """
        Aggiunge un'immagine come QLabel con una QPixmap.
        - path: percorso file su disco (jpg, png, ico, ecc.)
        - data: in alternativa a path, byte grezzi dell'immagine già in
          memoria (es. cover_bytes ottenuti da AudioMetadataReader)
        - width/height: se specificati, l'immagine viene ridimensionata
        - keep_aspect: mantiene le proporzioni originali durante il resize

        Il QLabel restituito ha un pixmap "fisso": per cambiarlo dopo, usa
        set_image().
        """
        lbl = QLabel()
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pixmap = QPixmap()
        if data is not None:
            pixmap.loadFromData(data)
        elif path is not None:
            pixmap = QPixmap(path)

        if width or height:
            w = width or pixmap.width()
            h = height or pixmap.height()
            mode = (Qt.AspectRatioMode.KeepAspectRatio if keep_aspect
                    else Qt.AspectRatioMode.IgnoreAspectRatio)
            pixmap = pixmap.scaled(w, h, mode, Qt.TransformationMode.SmoothTransformation)

        lbl.setPixmap(pixmap)
        return self.add_widget(lbl, name=name, object_name=object_name, **kwargs)

    def set_image(self, label, path=None, data=None, width=None, height=None, keep_aspect=True):
        """Aggiorna l'immagine di una QLabel già creata con add_image()."""
        pixmap = QPixmap()
        if data is not None:
            pixmap.loadFromData(data)
        elif path is not None:
            pixmap = QPixmap(path)

        if width or height:
            w = width or pixmap.width()
            h = height or pixmap.height()
            mode = (Qt.AspectRatioMode.KeepAspectRatio if keep_aspect
                    else Qt.AspectRatioMode.IgnoreAspectRatio)
            pixmap = pixmap.scaled(w, h, mode, Qt.TransformationMode.SmoothTransformation)
        label.setPixmap(pixmap)

    def add_spacing(self, size=20):
        if isinstance(self._layout, (QVBoxLayout, QHBoxLayout)):
            self._layout.addSpacing(size)

    def add_stretch(self, stretch=1):
        if isinstance(self._layout, (QVBoxLayout, QHBoxLayout)):
            self._layout.addStretch(stretch)

    def set_column_stretch(self, col, stretch):
        if isinstance(self._layout, QGridLayout):
            self._layout.setColumnStretch(col, stretch)

    def set_row_stretch(self, row, stretch):
        if isinstance(self._layout, QGridLayout):
            self._layout.setRowStretch(row, stretch)

    def set_spacing(self, spacing):
        """Distanza (in px) tra i widget dentro questo layout."""
        self._layout.setSpacing(spacing)

    def set_horizontal_spacing(self, spacing):
        """Solo per layout a griglia: distanza tra colonne."""
        if isinstance(self._layout, QGridLayout):
            self._layout.setHorizontalSpacing(spacing)

    def set_vertical_spacing(self, spacing):
        """Solo per layout a griglia: distanza tra righe."""
        if isinstance(self._layout, QGridLayout):
            self._layout.setVerticalSpacing(spacing)

    def set_margins(self, left, top=None, right=None, bottom=None):
        """
        Margine (in px) tra il bordo del container e i widget interni.
        Puoi passare un solo valore per applicarlo su tutti e 4 i lati,
        oppure i 4 valori singolarmente (left, top, right, bottom).
        """
        if top is None:
            top = right = bottom = left
        self._layout.setContentsMargins(left, top, right, bottom)

    def add_container(self, layout="vertical", name=None, object_name=None,
                       max_cols=4, spacing=None, margins=None, **kwargs):
        """
        Crea un nuovo Container (con il proprio layout indipendente),
        lo aggiunge a questo container/finestra e lo restituisce, così
        puoi popolarlo separatamente con i suoi add_button/add_label/ecc.
        """
        container = Container(layout=layout, max_cols=max_cols, spacing=spacing, margins=margins)
        self.add_widget(container, name=name, object_name=object_name, **kwargs)
        return container

    def add_scroll_container(self, layout="vertical", name=None,
                              object_name=None, scroll_object_name=None,
                              max_cols=4, spacing=None, margins=None,
                              horizontal_scroll=False, **kwargs):
        """
        Aggiunge un'area scorrevole (QScrollArea) e al suo interno un
        Container: restituisce il Container, così ci aggiungi widget
        normalmente (add_button, add_label, add_image, ecc.) e diventano
        automaticamente scorrevoli quando superano lo spazio disponibile.

        - object_name: nome QSS del Container interno (il contenuto)
        - scroll_object_name: nome QSS della QScrollArea stessa (il "riquadro")
        - horizontal_scroll: se True permette anche lo scroll orizzontale
        """
        container = Container(layout=layout, max_cols=max_cols, spacing=spacing, margins=margins)
        if object_name:
            container.setObjectName(object_name)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        if scroll_object_name:
            scroll.setObjectName(scroll_object_name)
        if not horizontal_scroll:
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(container)

        if name:
            self._widgets[name] = container
        self._add_to_layout(scroll, **kwargs)
        return container

    def get(self, name):
        """Recupera un widget registrato con name=... (cerca anche nei container annidati)."""
        if name in self._widgets:
            return self._widgets[name]
        for w in self._widgets.values():
            if isinstance(w, LayoutMixin):
                found = w.get(name)
                if found is not None:
                    return found
        return None


class Container(QWidget, LayoutMixin):
    """Un pannello con il proprio layout, da annidare dentro altri container."""

    def __init__(self, layout="vertical", max_cols=4, spacing=None, margins=None):
        super().__init__()
        self._init_layout(layout, max_cols=max_cols, spacing=spacing, margins=margins)
        self.setLayout(self._layout)


class QtWindow(QMainWindow, LayoutMixin):
    """Finestra Qt6 flessibile: è essa stessa un container di primo livello."""

    def __init__(self, title="Finestra", width=800, height=600, layout="vertical",
                 max_cols=4, spacing=None, margins=None):
        super().__init__()
        self.setWindowTitle(title)
        self.resize(width, height)

        self._central = QWidget()
        self._central.setObjectName("centralWidget")
        self.setCentralWidget(self._central)

        self._init_layout(layout, max_cols=max_cols, spacing=spacing, margins=margins)
        self._central.setLayout(self._layout)

    # --- QSS ---
    def apply_qss_string(self, qss: str):
        self.setStyleSheet(qss)

    def apply_qss_file(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            self.setStyleSheet(f.read())

    def apply_qss_to_app(self, qss: str):
        app = QApplication.instance()
        if app:
            app.setStyleSheet(qss)