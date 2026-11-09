import random
import re
import configparser
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
 
from PySide6.QtCore import QObject, Qt, QUrl, Signal
from PySide6.QtGui import QAction, QIcon, QImage, QPixmap
from PySide6.QtMultimedia import QAudioOutput, QMediaMetaData, QMediaPlayer
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPushButton,
    QSizePolicy,
    QSlider,
    QStackedWidget,
    QStyle,
    QVBoxLayout,
    QWidget,
)
 
AUDIO_EXT = {".mp3", ".flac", ".ogg", ".opus", ".wav", ".m4a", ".aac", ".wma"}
 
 
def fmt_time(ms: int) -> str:
    s = max(ms, 0) // 1000
    return f"{s // 60:02d}:{s % 60:02d}"

@dataclass
class Track:
    path: Path
    title: str = ""
    artist: str = "Unknown artist"
 
    def __post_init__(self):
        if not self.title:
            self.title = self.path.stem
 
 
class Playlist(QObject):
 
    currentChanged = Signal(int)
    tracksAdded = Signal(int, list)
 
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tracks: list[Track] = []
        self._current = -1
        self.shuffle = False
        self.repeat = False

    def __len__(self):
        return len(self._tracks)
 
    @property
    def current_index(self) -> int:
        return self._current
 
    @property
    def current_track(self) -> Optional[Track]:
        return self._tracks[self._current] if 0 <= self._current < len(self) else None
 
    def track(self, index: int) -> Track:
        return self._tracks[index]
 
    def add_paths(self, paths: list[Path]) -> None:
        known = {t.path for t in self._tracks}
        new = [Track(p) for p in paths if p not in known]
        if not new:
            return
        first = len(self._tracks)
        self._tracks.extend(new)
        self.tracksAdded.emit(first, new)
 
    def set_current(self, index: int) -> None:
        if 0 <= index < len(self):
            self._current = index
            self.currentChanged.emit(index)
 
    def update_current_info(self, title: str, artist: str) -> None:
        t = self.current_track
        if t:
            if title:
                t.title = title
            if artist:
                t.artist = artist

    def next_index(self, auto: bool = False) -> Optional[int]:
        n = len(self)
        if n == 0:
            return None
        if self.shuffle:
            if n == 1:
                return 0 if (self.repeat or not auto) else None
            return random.choice([i for i in range(n) if i != self._current])
        nxt = self._current + 1
        if nxt >= n:
            return 0 if (self.repeat or not auto) else None
        return nxt
 
    def prev_index(self) -> Optional[int]:
        n = len(self)
        return None if n == 0 else (self._current - 1) % n
 
 
class AudioEngine(QObject):
 
    positionChanged = Signal(int)
    durationChanged = Signal(int)
    playingChanged = Signal(bool)
    endOfMedia = Signal()
    metadataChanged = Signal(str, str, object)  #Title,Artist,Img
 
    def __init__(self, parent=None):
        super().__init__(parent)
        self._player = QMediaPlayer(self)
        self._output = QAudioOutput(self)
        self._player.setAudioOutput(self._output)
 
        self._player.positionChanged.connect(lambda ms: self.positionChanged.emit(int(ms)))
        self._player.durationChanged.connect(lambda ms: self.durationChanged.emit(int(ms)))
        self._player.playbackStateChanged.connect(
            lambda s: self.playingChanged.emit(s == QMediaPlayer.PlayingState)
        )
        self._player.mediaStatusChanged.connect(self._on_status)
        self._player.metaDataChanged.connect(self._on_metadata)
 
    def load(self, path: Path) -> None:
        self._player.setSource(QUrl.fromLocalFile(str(path)))
 
    def play(self) -> None:
        self._player.play()
 
    def pause(self) -> None:
        self._player.pause()
 
    def toggle(self) -> None:
        if self.is_playing:
            self.pause()
        else:
            self.play()
 
    def seek(self, ms: int) -> None:
        self._player.setPosition(ms)
 
    def set_muted(self, muted: bool) -> None:
        self._output.setMuted(muted)
 
    @property
    def is_playing(self) -> bool:
        return self._player.playbackState() == QMediaPlayer.PlayingState
 
    @property
    def position(self) -> int:
        return self._player.position()
 
    def _on_status(self, status) -> None:
        if status == QMediaPlayer.EndOfMedia:
            self.endOfMedia.emit()
 
    def _on_metadata(self) -> None:
        md = self._player.metaData()
        title = md.value(QMediaMetaData.Title) or ""
        artist = md.value(QMediaMetaData.ContributingArtist) or md.value(QMediaMetaData.AlbumArtist) or ""
        if isinstance(artist, (list, tuple)):
            artist = ", ".join(map(str, artist))
        img = md.value(QMediaMetaData.ThumbnailImage) or md.value(QMediaMetaData.CoverArtImage)
        if not (isinstance(img, QImage) and not img.isNull()):
            img = None
        self.metadataChanged.emit(str(title), str(artist), img)
 
class Icons:
 
    @staticmethod
    def get(theme_name: str, fallback: QStyle.StandardPixmap) -> QIcon:
        icon = QIcon.fromTheme(theme_name)
        if icon.isNull():
            icon = QApplication.style().standardIcon(fallback)
        return icon
 
 
class CoverWidget(QLabel):
 
    DEFAULT_SIZE = 400
 
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(self.DEFAULT_SIZE, self.DEFAULT_SIZE)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._pixmap = QPixmap()
        self.clear_cover()
 
    def set_image(self, image: QImage) -> None:
        self._pixmap = QPixmap.fromImage(image)
        self._rescale()
 
    def clear_cover(self) -> None:
        icon = Icons.get("image-missing", QStyle.SP_FileIcon)
        self._pixmap = icon.pixmap(self.DEFAULT_SIZE, self.DEFAULT_SIZE)
        self._rescale()
 
    def _rescale(self) -> None:
        if self._pixmap.isNull():
            return
        side = min(self.width(), self.height()) or self.DEFAULT_SIZE
        self.setPixmap(self._pixmap.scaled(side, side, Qt.KeepAspectRatio, Qt.SmoothTransformation))
 
    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._rescale()
 
 
class TrackInfoWidget(QWidget):
 
    def __init__(self, parent=None):
        super().__init__(parent)
        self._title = QLabel("Name-Song")
        self._title.setStyleSheet("font-size: 28px; font-weight: bold;")
        self._title.setWordWrap(True)
        self._artist = QLabel("Name-Artist")
        self._artist.setStyleSheet("font-style: italic;")
 
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._title)
        layout.addWidget(self._artist)
 
    def set_info(self, title: str, artist: str) -> None:
        self._title.setText(title)
        self._artist.setText(artist)
 
 
class SeekBar(QWidget):
 
    seekRequested = Signal(int)
 
    def __init__(self, parent=None):
        super().__init__(parent)
        self._slider = QSlider(Qt.Horizontal)
        self._slider.setRange(0, 0)
        self._time = QLabel("00:00")
        self._time.setStyleSheet("font-family: monospace; font-weight: bold;")
        self._time.setMinimumWidth(45)
 
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.addWidget(self._slider, 1)
        layout.addWidget(self._time)
 
        self._slider.sliderMoved.connect(self.seekRequested)
        self._slider.sliderReleased.connect(lambda: self.seekRequested.emit(self._slider.value()))
 
    def set_position(self, ms: int) -> None:
        if not self._slider.isSliderDown():
            self._slider.setValue(ms)
        self._time.setText(fmt_time(ms))
 
    def set_duration(self, ms: int) -> None:
        self._slider.setRange(0, ms)
        self._time.setToolTip(f"Total: {fmt_time(ms)}")
 
 
class ControlBar(QWidget): 
    playClicked = Signal()
    prevClicked = Signal()
    nextClicked = Signal()
    shuffleToggled = Signal(bool)
    repeatToggled = Signal(bool)
    muteToggled = Signal(bool)
 
    def __init__(self, parent=None):
        super().__init__(parent)
        self._shuffle = self._make_button(checkable=True)
        self._prev = self._make_button()
        self._play = self._make_button()
        self._next = self._make_button()
        self._repeat = self._make_button(checkable=True)
        self._mute = self._make_button(checkable=True)
 
        self._shuffle.setIcon(Icons.get("media-playlist-shuffle", QStyle.SP_BrowserReload))
        self._prev.setIcon(Icons.get("media-skip-backward", QStyle.SP_MediaSkipBackward))
        self._next.setIcon(Icons.get("media-skip-forward", QStyle.SP_MediaSkipForward))
        self._repeat.setIcon(Icons.get("media-playlist-repeat", QStyle.SP_BrowserReload))
        self.set_playing(False)
        self._refresh_mute_icon(False)
 
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addStretch(1)
        for b in (self._shuffle, self._prev, self._play, self._next, self._repeat, self._mute):
            layout.addWidget(b)
        layout.addStretch(2)
 
        self._play.clicked.connect(self.playClicked)
        self._prev.clicked.connect(self.prevClicked)
        self._next.clicked.connect(self.nextClicked)
        self._shuffle.toggled.connect(self.shuffleToggled)
        self._repeat.toggled.connect(self.repeatToggled)
        self._mute.toggled.connect(self._on_mute)
 
    @staticmethod
    def _make_button(checkable: bool = False) -> QPushButton:
        b = QPushButton()
        b.setCheckable(checkable)
        return b
 
    def set_playing(self, playing: bool) -> None:
        if playing:
            self._play.setIcon(Icons.get("media-playback-pause", QStyle.SP_MediaPause))
        else:
            self._play.setIcon(Icons.get("media-playback-start", QStyle.SP_MediaPlay))
 
    def _on_mute(self, muted: bool) -> None:
        self._refresh_mute_icon(muted)
        self.muteToggled.emit(muted)
 
    def _refresh_mute_icon(self, muted: bool) -> None:
        if muted:
            self._mute.setIcon(Icons.get("audio-volume-muted", QStyle.SP_MediaVolumeMuted))
        else:
            self._mute.setIcon(Icons.get("audio-volume-high", QStyle.SP_MediaVolume))
 
 
class SourceMenu(QMenu):
 
    pathsSelected = Signal(list)  #list[Path]
 
    def __init__(self, parent=None):
        super().__init__(parent)
        act_folder = QAction("Folder...", self)
        act_files = QAction("File(s)...", self)
        act_folder.triggered.connect(self._choose_folder)
        act_files.triggered.connect(self._choose_files)
        self.addAction(act_folder)
        self.addAction(act_files)
 
    def _choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self.parentWidget(), "Select folder")
        if folder:
            files = sorted(p for p in Path(folder).rglob("*") if p.suffix.lower() in AUDIO_EXT)
            self.pathsSelected.emit(files)
 
    def _choose_files(self) -> None:
        exts = " ".join(f"*{e}" for e in sorted(AUDIO_EXT))
        files, _ = QFileDialog.getOpenFileNames(self.parentWidget(), "Select files", "", f"Audio ({exts})")
        if files:
            self.pathsSelected.emit([Path(f) for f in files])
 
 
class EmptyPage(QWidget):
 
    def __init__(self, menu: QMenu, parent=None):
        super().__init__(parent)
        folder = QLabel()
        folder.setAlignment(Qt.AlignCenter)
        folder.setPixmap(Icons.get("folder-open", QStyle.SP_DirOpenIcon).pixmap(64, 64))
 
        message = QLabel("No Music Avalible")
        message.setAlignment(Qt.AlignCenter)
        message.setStyleSheet("font-weight: bold;")
 
        button = QPushButton("Select Folder or File")
        button.setMenu(menu)
 
        layout = QVBoxLayout(self)
        layout.addStretch(2)
        layout.addWidget(folder)
        layout.addSpacing(30)
        layout.addWidget(message)
        layout.addSpacing(30)
        layout.addWidget(button)
        layout.addStretch(3)
 
 
class ListPage(QWidget):
 
    trackActivated = Signal(int)  #Playlist Index
 
    def __init__(self, menu: QMenu, parent=None):
        super().__init__(parent)
        self._search = QLineEdit()
        self._search.setPlaceholderText("Search a song...")
        self._search.setClearButtonEnabled(True)
        self._search.addAction(Icons.get("edit-find", QStyle.SP_FileDialogContentsView),
                               QLineEdit.TrailingPosition)
        self._list = QListWidget()
        add_button = QPushButton("Add Folder or File")
        add_button.setMenu(menu)
 
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._search)
        layout.addWidget(self._list, 1)
        layout.addWidget(add_button)
 
        self._search.textChanged.connect(self._filter)
        self._list.itemDoubleClicked.connect(lambda it: self.trackActivated.emit(it.data(Qt.UserRole)))
 
    def add_tracks(self, first_index: int, tracks: list) -> None:
        for offset, track in enumerate(tracks):
            item = QListWidgetItem(track.title)
            item.setData(Qt.UserRole, first_index + offset)
            item.setToolTip(str(track.path))
            self._list.addItem(item)
        self._filter(self._search.text())
 
    def highlight(self, index: int) -> None:
        for i in range(self._list.count()):
            item = self._list.item(i)
            is_current = item.data(Qt.UserRole) == index
            font = item.font()
            font.setBold(is_current)
            item.setFont(font)
            if is_current:
                self._list.setCurrentItem(item)
 
    def rename(self, index: int, title: str) -> None:
        for i in range(self._list.count()):
            item = self._list.item(i)
            if item.data(Qt.UserRole) == index:
                item.setText(title)
 
    def _filter(self, text: str) -> None:
        text = text.lower().strip()
        for i in range(self._list.count()):
            item = self._list.item(i)
            item.setHidden(text not in item.text().lower())
 
 
class PlaylistPanel(QWidget):
 
    pathsSelected = Signal(list)
    trackActivated = Signal(int)
 
    EMPTY, FULL = 0, 1
 
    def __init__(self, parent=None):
        super().__init__(parent)
        self._menu = SourceMenu(self)
        self._menu.pathsSelected.connect(self.pathsSelected)
 
        title = QLabel("Music List")
        title.setStyleSheet("font-weight: bold;")
        note = QLabel()
        note.setPixmap(Icons.get("audio-x-generic", QStyle.SP_MediaPlay).pixmap(16, 16))
 
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 5, 0)
        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(note)
 
        self._empty = EmptyPage(self._menu)
        self._list = ListPage(self._menu)
        self._list.trackActivated.connect(self.trackActivated)
 
        self._stack = QStackedWidget()
        self._stack.addWidget(self._empty)
        self._stack.addWidget(self._list)
 
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 5, 5)
        layout.addLayout(header)
        layout.addWidget(self._stack, 1)
 
    def add_tracks(self, first_index: int, tracks: list) -> None:
        self._list.add_tracks(first_index, tracks)
        self._stack.setCurrentIndex(self.FULL)
 
    def highlight(self, index: int) -> None:
        self._list.highlight(index)
 
    def rename(self, index: int, title: str) -> None:
        self._list.rename(index, title)
 
class MainWindow(QWidget):
 
    RESTART_THRESHOLD_MS = 3000
 
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AR Media Player")
        self.resize(900, 700)
        self.playlist = Playlist(self)
        self.engine = AudioEngine(self)
        self.cover = CoverWidget()
        self.info = TrackInfoWidget()
        self.seekbar = SeekBar()
        self.controls = ControlBar()
        self.panel = PlaylistPanel()
        self._build_layout()
        self._connect()
 
    def _build_layout(self) -> None:
        left = QVBoxLayout()
        left.setContentsMargins(0, 0, 0, 10)
        left.addWidget(self.cover, 1)
        left.addWidget(self.info)
        left.addSpacing(15)
        left.addWidget(self.seekbar)
        left.addSpacing(15)
        left.addWidget(self.controls)
        left_w = QWidget()
        left_w.setLayout(left)
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(10)
        root.addWidget(left_w, 3)
        root.addWidget(self.panel, 2)
 
    def _connect(self) -> None:
        #panel -> playlist
        self.panel.pathsSelected.connect(self.playlist.add_paths)
        self.panel.trackActivated.connect(self.play_index)
        #playlist -> UI
        self.playlist.tracksAdded.connect(self._on_tracks_added)
        #controls -> azioni
        self.controls.playClicked.connect(self.toggle_play)
        self.controls.nextClicked.connect(self.next_track)
        self.controls.prevClicked.connect(self.prev_track)
        self.controls.shuffleToggled.connect(lambda v: setattr(self.playlist, "shuffle", v))
        self.controls.repeatToggled.connect(lambda v: setattr(self.playlist, "repeat", v))
        self.controls.muteToggled.connect(self.engine.set_muted)
        #seekbar -> audio
        self.seekbar.seekRequested.connect(self.engine.seek)
        #audio -> UI
        self.engine.positionChanged.connect(self.seekbar.set_position)
        self.engine.durationChanged.connect(self.seekbar.set_duration)
        self.engine.playingChanged.connect(self.controls.set_playing)
        self.engine.endOfMedia.connect(self._on_end_of_media)
        self.engine.metadataChanged.connect(self._on_metadata)
 
    def play_index(self, index: int) -> None:
        self.playlist.set_current(index)
        track = self.playlist.current_track
        if track is None:
            return
        self.info.set_info(track.title, track.artist)
        self.cover.clear_cover()
        self.engine.load(track.path)
        self.engine.play()
        self.panel.highlight(index)
 
    def toggle_play(self) -> None:
        if len(self.playlist) == 0:
            return
        if self.playlist.current_index < 0:
            self.play_index(0)
        else:
            self.engine.toggle()
 
    def next_track(self) -> None:
        idx = self.playlist.next_index()
        if idx is not None:
            self.play_index(idx)
 
    def prev_track(self) -> None:
        if self.engine.position > self.RESTART_THRESHOLD_MS:
            self.engine.seek(0)
            return
        idx = self.playlist.prev_index()
        if idx is not None:
            self.play_index(idx)
 
    # --- reazioni a eventi ---
    def _on_tracks_added(self, first_index: int, tracks: list) -> None:
        self.panel.add_tracks(first_index, tracks)
        if self.playlist.current_index < 0:
            self.play_index(first_index)
 
    def _on_end_of_media(self) -> None:
        idx = self.playlist.next_index(auto=True)
        if idx is not None:
            self.play_index(idx)
 
    def _on_metadata(self, title: str, artist: str, image) -> None:
        self.playlist.update_current_info(title, artist)
        track = self.playlist.current_track
        if track is None:
            return
        self.info.set_info(track.title, track.artist)
        self.panel.rename(self.playlist.current_index, track.title)
        if image is not None:
            self.cover.set_image(image)


def carica_stile(app: QApplication, qss_path: str, conf_path: str) -> None:
    conf = configparser.ConfigParser()
    conf.read(conf_path, encoding="utf-8")
    colori = dict(conf["colors"]) if "colors" in conf else {}
    with open(qss_path, encoding="utf-8") as f:
        qss = f.read()
    hex_ok = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
    def sostituisci(m: re.Match) -> str:
        nome = m.group(1)
        valore = colori.get(nome)
        if valore is None or not hex_ok.match(valore):
            return m.group(0)
        return valore
    qss = re.sub(r"@([A-Za-z_][A-Za-z0-9_]*)", sostituisci, qss)
    app.setStyleSheet(qss)

def dir_config() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA",Path.home()/"AppData"/"Roaming"))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME",Path.home()/".config"))
    return base / "AR-media-player"
if __name__ == "__main__":
    app = QApplication(sys.argv)
    #config_dir = dir_config()
    #config_dir.mkdir(parents=True,exist_ok=True)
    
    carica_stile(app,"AR_Medias/style/styles.qss","AR_Mediastyle/confcolor.conf")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
 