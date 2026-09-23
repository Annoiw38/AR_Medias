import os
import tkinter as tk
from tkinter import filedialog
from PIL import Image,ImageTk
import pygame

class AR_Medias:
	def __init__(self,root):
		pygame.mixer.init()
		self.root=root
		self.root.title("AR Medias Player")
		self.root.geometry("400x350")
		self.root.config(bg="#1e1e1e")
		self.current_song=None
		self.load_images()
		self.create_widgets()
	def load_images(self):
		play_img=Image.open("assets/play.png").resize((40,40))
		pause_img=Image.open("assets/pause.png").resize((40,40))
		self.play_icon=ImageTk.PhotoImage(play_img)
		self.pause_icon=ImageTk.PhotoImage(pause_img)
	def create_widgets(self):
		self.song_label=tk.Label(self.root,text="No song selected",font=("Helvetica",11,"bold"),fg="#ffffff",bg="#1e1e1e",wraplength=350)
		self.song_label.pack(pady=30)
		self.select_btn=tk.Button(self.root,text="Browse Music",command=self.load_song,bg="#007acc",fg="white",font=("Helvetica",10,"bold"),relief="flat",padx=10,pady=5)
		self.select_btn.pack(pady=10)
		controls_frame=tk.Frame(self.root,bg="#1e1e1e")
		controls_frame.pack(pady=20)
		self.play_btn=tk.Button(controls_frame,image=self.play_icon,command=self.play_song,bg="#1e1e1e",activebackground="#1e1e1e",bd=0)
		self.play_btn.grid(row=0,column=0,padx=15)
		self.stop_btn=tk.Button(controls_frame,image=self.pause_icon,command=self.stop_song,bg="#1e1e1e",activebackground="#1e1e1e",bd=0)
		self.stop_btn.grid(row=0,column=1,padx=15)
	def load_song(self):
		file_path=filedialog.askopenfilename(initialdir="songs",title="Select Audio Track",filetypes=(("Audio Files","*.mp3 *.wav"),))
		if file_path:
			self.current_song=file_path
			song_name=os.path.basename(file_path)
			self.song_label.config(text=f"Now Playing:\n{song_name}")
	def play_song(self):
		if self.current_song:
			pygame.mixer.music.load(self.current_song)
			pygame.mixer.music.play()
	def stop_song(self):
		pygame.mixer.music.stop()

if __name__=="__main__":
	root=tk.Tk()
	app=AR_Medias(root)
	root.mainloop()