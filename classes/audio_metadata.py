"""
Modulo indipendente per leggere metadati (titolo, artista, album, genere,
traccia, durata) e copertina da file audio (mp3, flac, ogg, m4a).

Non dipende da PyQt6: puoi usarlo da solo, in uno script, in un test,
o insieme alla classe QtWindow per popolare le label della UI.

Richiede: pip install mutagen
"""

from dataclasses import dataclass
from typing import Optional

import mutagen
from mutagen.id3 import APIC


@dataclass
class SongMetadata:
    title: str = ""
    artist: str = ""
    album: str = ""
    genre: str = ""
    track_number: Optional[int] = None
    duration_seconds: float = 0.0
    cover_bytes: Optional[bytes] = None   # dati grezzi dell'immagine (jpg/png)
    cover_mime: Optional[str] = None      # es. "image/jpeg"

    @property
    def has_cover(self) -> bool:
        return self.cover_bytes is not None


class AudioMetadataReader:
    """Legge i metadati di un file audio senza doverlo riprodurre."""

    @staticmethod
    def read(path: str) -> SongMetadata:
        meta = SongMetadata()
        audio = mutagen.File(path)

        if audio is None:
            return meta  # formato non riconosciuto o file corrotto

        meta.duration_seconds = getattr(audio.info, "length", 0.0) or 0.0
        lower = path.lower()

        if lower.endswith(".mp3"):
            AudioMetadataReader._read_mp3(audio, meta)
        elif lower.endswith(".flac"):
            AudioMetadataReader._read_flac(audio, meta)
        elif lower.endswith(".ogg"):
            AudioMetadataReader._read_ogg(audio, meta)
        elif lower.endswith((".m4a", ".mp4")):
            AudioMetadataReader._read_mp4(audio, meta)
        else:
            # fallback generico: prova comunque a leggere i tag comuni
            AudioMetadataReader._read_generic(audio, meta)

        return meta

    # ------------------------------------------------------------------ #
    @staticmethod
    def _first(tags, key, default=""):
        val = tags.get(key)
        if not val:
            return default
        return str(val[0]) if isinstance(val, list) else str(val)

    @staticmethod
    def _read_mp3(audio, meta: SongMetadata):
        tags = audio.tags
        if not tags:
            return
        meta.title = str(tags.get("TIT2", ""))
        meta.artist = str(tags.get("TPE1", ""))
        meta.album = str(tags.get("TALB", ""))
        meta.genre = str(tags.get("TCON", ""))

        track = tags.get("TRCK")
        if track:
            try:
                meta.track_number = int(str(track).split("/")[0])
            except ValueError:
                pass

        for tag in tags.values():
            if isinstance(tag, APIC):
                meta.cover_bytes = tag.data
                meta.cover_mime = tag.mime
                break

    @staticmethod
    def _read_flac(audio, meta: SongMetadata):
        meta.title = AudioMetadataReader._first(audio, "title")
        meta.artist = AudioMetadataReader._first(audio, "artist")
        meta.album = AudioMetadataReader._first(audio, "album")
        meta.genre = AudioMetadataReader._first(audio, "genre")

        track = AudioMetadataReader._first(audio, "tracknumber")
        if track:
            try:
                meta.track_number = int(track.split("/")[0])
            except ValueError:
                pass

        if getattr(audio, "pictures", None):
            pic = audio.pictures[0]
            meta.cover_bytes = pic.data
            meta.cover_mime = pic.mime

    @staticmethod
    def _read_ogg(audio, meta: SongMetadata):
        meta.title = AudioMetadataReader._first(audio, "title")
        meta.artist = AudioMetadataReader._first(audio, "artist")
        meta.album = AudioMetadataReader._first(audio, "album")
        meta.genre = AudioMetadataReader._first(audio, "genre")
        # Ogg Vorbis di solito non incorpora la cover nello stesso modo;
        # spesso è in un file separato o come immagine base64 in METADATA_BLOCK_PICTURE.

    @staticmethod
    def _read_mp4(audio, meta: SongMetadata):
        meta.title = AudioMetadataReader._first(audio, "\xa9nam")
        meta.artist = AudioMetadataReader._first(audio, "\xa9ART")
        meta.album = AudioMetadataReader._first(audio, "\xa9alb")
        meta.genre = AudioMetadataReader._first(audio, "\xa9gen")

        covers = audio.get("covr")
        if covers:
            cover = covers[0]
            meta.cover_bytes = bytes(cover)
            try:
                is_png = cover.imageformat == cover.FORMAT_PNG
            except AttributeError:
                is_png = False
            meta.cover_mime = "image/png" if is_png else "image/jpeg"

    @staticmethod
    def _read_generic(audio, meta: SongMetadata):
        try:
            meta.title = AudioMetadataReader._first(audio, "title")
            meta.artist = AudioMetadataReader._first(audio, "artist")
            meta.album = AudioMetadataReader._first(audio, "album")
        except Exception:
            pass

    # ------------------------------------------------------------------ #
    @staticmethod
    def cover_to_qpixmap(meta: SongMetadata):
        """
        Converte i byte della cover in QPixmap. Richiede PyQt6, ma
        l'import è fatto qui dentro apposta: il resto del modulo
        (lettura dei tag) resta usabile anche senza PyQt6 installato.
        """
        if not meta.has_cover:
            return None
        from PyQt6.QtGui import QPixmap
        pixmap = QPixmap()
        pixmap.loadFromData(meta.cover_bytes)
        return pixmap

    @staticmethod
    def save_cover(meta: SongMetadata, output_path: str):
        """Salva la cover su disco come file immagine."""
        if not meta.has_cover:
            return False
        with open(output_path, "wb") as f:
            f.write(meta.cover_bytes)
        return True


"""if __name__ == "__main__":
    # Esempio d'uso da riga di comando: python audio_metadata.py canzone.mp3
    import sys
    if len(sys.argv) < 2:
        print("Uso: python audio_metadata.py <file_audio>")
        sys.exit(1)

    meta = AudioMetadataReader.read(sys.argv[1])
    print("Titolo :", meta.title)
    print("Artista:", meta.artist)
    print("Album  :", meta.album)
    print("Genere :", meta.genre)
    print("Traccia:", meta.track_number)
    print("Durata :", round(meta.duration_seconds, 1), "sec")
    print("Cover  :", "presente" if meta.has_cover else "assente")
    """