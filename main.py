import sys
import os
from classes.window import QtWindow
from PyQt6.QtWidgets import QApplication, QFileDialog
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput, QMediaMetaData
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QImage,QPixmap

if __name__ == "__main__":
    path = "/home/fabrizio-computer/Documenti/env_annoiw_project/annoi_project/AR_Medias/style/styles.qss"
    with open(path,"r") as file:
        content = file.read() 
    
    icon_path : list = [
        "/home/fabrizio-computer/Documenti/env_annoiw_project/annoi_project/AR_Medias/assets/media-player-control/previous.ico",
        "/home/fabrizio-computer/Documenti/env_annoiw_project/annoi_project/AR_Medias/assets/media-player-control/play.ico",
        "/home/fabrizio-computer/Documenti/env_annoiw_project/annoi_project/AR_Medias/assets/media-player-control/next.ico"
    ]
    app = QApplication(sys.argv)

    finestra = QtWindow(title="AR mdeia player", width=500, height=250, layout="grid",spacing=20,margins=1)
    panelMusic = finestra.add_container(layout="vertical",object_name="panel_music", spacing=0,margins=0)
    panelMetaData = panelMusic.add_container(layout="vertical",object_name="panel_meta_data", spacing=0,margins=0)
    panelMediaPlayerControl = panelMusic.add_container(layout="horizontal",object_name="panel_media_player_control", spacing=0,margins=0)
    panelMetaData.add_image(path="/home/fabrizio-computer/Documenti/env_annoiw_project/annoi_project/AR_Medias/assets/no_image.png",name="albumImage",object_name="album_image")
    panelMetaData.add_label("None music",name="musicTitle",object_name="music_title")
    panelMetaData.add_label("None Artist",name="artistName",object_name="artist_name")
    

    finestra.apply_qss_string(content)
    finestra.show()
    sys.exit(app.exec())