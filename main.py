import sys
import os
from pathlib import Path
from classes.window import QtWindow
from PyQt6.QtWidgets import QApplication, QFileDialog
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput, QMediaMetaData
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QImage,QPixmap
from classes.audio_metadata import AudioMetadataReader

if __name__ == "__main__":
    BASE_DIR = Path(__file__).resolve().parent
    path = BASE_DIR / "style/styles.qss"
    with open(path,"r") as file:
        content = file.read() 
    
    icon_path : list = [
        str(BASE_DIR)+"/assets/media-player-control/previous.ico",
        str(BASE_DIR)+"/assets/media-player-control/play.ico",
        str(BASE_DIR)+"/assets/media-player-control/next.ico"
    ]
    app = QApplication(sys.argv)

    finestra = QtWindow(title="AR mdeia player", width=800, height=600, layout="horizontal",spacing=0,margins=0)


    panelMusic = finestra.add_container(layout="vertical",object_name="panel_music", spacing=0,margins=0)
    panelMetaData = panelMusic.add_container(layout="vertical",object_name="panel_meta_data", spacing=0,margins=0)
    panelMediaPlayerControl = panelMusic.add_container(layout="horizontal",object_name="panel_media_player_control", spacing=0,margins=0)
    panelMusicList = finestra.add_container(layout="vertical",object_name="panel_musci_list",spacing=0,margins=0)
    panelMetaData.add_label("                  ")
    panelMetaData.add_label("                  ")
    panelMetaData.add_label("                  ")
    panelMetaData.add_image(path=str(BASE_DIR)+"/assets/no_image.png",name="albumImage",object_name="album_image")
    panelMetaData.add_label("   None music",name="musicTitle",object_name="music_title")
    panelMetaData.add_label("   None Artist",name="artistName",object_name="artist_name")
    panelMediaPlayerControl.add_button("",name="previousBtn",object_name="control_btn",icon_p=icon_path[0])
    panelMediaPlayerControl.add_button("",name="playBtn",object_name="control_btn",icon_p=icon_path[1])
    panelMediaPlayerControl.add_button("",name="nextBtn",object_name="control_btn",icon_p=icon_path[2])
    panelMetaData.add_label("                  ")
    panelMetaData.add_label("                  ")
    panelMetaData.add_label("                  ")
    panelMusicList.add_label("Music List")
    panelEmptyList = panelMusicList.add_container(layout="vertical",object_name="panel_empty_list")
    panelEmptyList.add_label("󰷏",name="emptyLogo",object_name="empty_logo")
    panelEmptyList.get("emptyLogo")
    panelEmptyList.add_button("Add Folder",name="addFolder",object_name="add_folder")
    panelEmptyList.add_label("                  ")
    panelEmptyList.add_label("                  ")
    panelEmptyList.add_label("                  ")
    
    finestra.apply_qss_string(content)
    finestra.show()
    sys.exit(app.exec())