import dearpygui.dearpygui as dpg
import ntpath
import json
from mutagen.mp3 import MP3
from tkinter import Tk,filedialog
import threading
import pygame
import time
import random
import os
import atexit
import webbrowser
pygame.init()  # Initializes all imported pygame modules

dpg.create_context()
dpg.create_viewport(
	title="Rainy Music Freddy-Edition",
	large_icon="icon.ico",
	small_icon="icon.ico",
	decorated=True,   # Standard-Titelbalken bleibt erhalten
	always_on_top=False  # Fenster bleibt im Hintergrund wenn nötig
)
dpg.set_viewport_clear_color((0, 0, 0))  # sets window content area to black

pygame.mixer.init()
for event in pygame.event.get():
	if event.type == pygame.USEREVENT:
		if event.code == pygame.USEREVENT:
			next()
global state
state=None

global no
no = 0

_DEFAULT_MUSIC_VOLUME = 0.5
pygame.mixer.music.set_volume(0.5)
def event_listener():
	while True:
		for event in pygame.event.get():
			if event.type == pygame.USEREVENT:
				next()  # this advances to the next song
		time.sleep(0.1)

# Start the event listener thread
event_thread = threading.Thread(target=event_listener, daemon=True)
event_thread.start()
def update_volume(sender, app_data):
	pygame.mixer.music.set_volume(app_data / 100.0)

def load_database():
	songs = json.load(open("data/songs.json", "r"))["songs"]
	for song in songs:
		filename = ntpath.basename(song["path"])
		label = f"{filename} [{song['duration']}]"

		dpg.add_button(
			label=label,
			callback=play,
			width=-1,
			height=25,
			user_data=song["path"].replace("\\", "/"),
			parent="list"
		)
		
		dpg.add_spacer(height=2, parent="list")

def update_database(filename: str):
	data = json.load(open("data/songs.json", "r"))

	# Prüfen, ob Song schon existiert
	if not any(song["path"] == filename for song in data["songs"]):
		audio = MP3(filename)
		duration = int(audio.info.length)
		formatted = f"{duration // 60}:{duration % 60:02d}"

		data["songs"].append({
			"path": filename,
			"duration": formatted
		})

		with open("data/songs.json", "w") as f:
			json.dump(data, f, indent=4)

def update_slider():
	global state
	audio = MP3(no)
	duration = int(audio.info.length)

	while pygame.mixer.music.get_busy() or state == 'paused':
		current_pos = pygame.mixer.music.get_pos() / 1000
		mins, secs = divmod(int(current_pos), 60)
		dpg.configure_item("current_time", default_value=f"{mins}:{secs:02d}")
		dpg.configure_item("pos", default_value=current_pos)
		dpg.configure_item("total_duration", default_value=f"{duration // 60}:{duration % 60:02d}")
		time.sleep(0.7)

	# After the song ends
	state = None
	dpg.configure_item("cstate", default_value="State: None")
	dpg.configure_item("csong", default_value="Now Playing : ")
	dpg.configure_item("play", label="Play")
	dpg.configure_item("pos", max_value=100)
	dpg.configure_item("pos", default_value=0)

def play(sender, app_data, user_data):
	global state, no

	if user_data:
		no = user_data

		# Load and play the selected audio file
		pygame.mixer.music.load(user_data)
		pygame.mixer.music.play()
		pygame.mixer.music.set_endevent(pygame.USEREVENT)

		# Get audio duration and configure the slider
		audio = MP3(user_data)
		dpg.configure_item(item="pos", max_value=audio.info.length)

		# Start slider update thread
		threading.Thread(target=update_slider, daemon=False).start()

		# Update UI elements
		if pygame.mixer.music.get_busy():
			dpg.configure_item("play", label="Pause")
			state = "playing"
			dpg.configure_item("cstate", default_value="State: Playing")
			dpg.configure_item("csong", default_value=f"Now Playing : {ntpath.basename(user_data)}")

def play_pause():
	global state,no
	if state=="playing":
		state="paused"
		pygame.mixer.music.pause()
		dpg.configure_item("play",label="Play")
		dpg.configure_item("cstate",default_value=f"State: Paused")
	elif state=="paused":
		state="playing"
		pygame.mixer.music.unpause()
		dpg.configure_item("play",label="Pause")
		dpg.configure_item("cstate",default_value=f"State: Playing")
	else:
		song = json.load(open("data/songs.json", "r"))["songs"]
		if song:
			song=random.choice(song)
			no = song
			pygame.mixer.music.load(song)
			pygame.mixer.music.play()
			thread=threading.Thread(target=update_slider,daemon=False).start()	
			dpg.configure_item("play",label="Pause")
			if pygame.mixer.music.get_busy():
				audio = MP3(song)
				dpg.configure_item(item="pos",max_value=audio.info.length)
				state="playing"
				dpg.configure_item("csong",default_value=f"Now Playing : {ntpath.basename(song)}")
				dpg.configure_item("cstate",default_value=f"State: Playing")

def pre():
	global state,no
	songs = json.load(open('data/songs.json','r'))["songs"]
	try:
		n = songs.index(no)
		if n == 0:
			n = len(songs)
		play(sender=any,app_data=any,user_data=songs[n-1])
	except:
		pass

def next():
	global state,no
	try:
		songs = json.load(open('data/songs.json','r'))["songs"]
		n = songs.index(no)
		if n == len(songs)-1:
			n = -1
		play(sender=any,app_data=any,user_data=songs[n+1])
	except:
		pass

def stop():
	global state
	pygame.mixer.music.stop()
	state=None

def format_length(filepath):
	audio = MP3(filepath)
	seconds = int(audio.info.length)
	minutes = seconds // 60
	seconds = seconds % 60
	return f"{minutes}:{seconds:02d}"

def format_length(filepath):
	audio = MP3(filepath)
	seconds = int(audio.info.length)
	minutes = seconds // 60
	seconds = seconds % 60
	return f"{minutes}:{seconds:02d}"

def add_files():
	data = json.load(open("data/songs.json", "r"))
	root = Tk()
	root.withdraw()
	filename = filedialog.askopenfilename(filetypes=[("Music Files", ("*.mp3", "*.wav", "*.ogg"))])
	root.quit()

	if filename.endswith((".mp3", ".wav", ".ogg")):
		if filename not in data["songs"]:
			update_database(filename)
			display_name = f"{ntpath.basename(filename)} [{format_length(filename)}]"
			dpg.add_button(label=display_name, callback=play, width=-1, height=25,
						   user_data=filename.replace("\\", "/"), parent="list")
			dpg.add_spacer(height=2, parent="list")

def add_folder():
	data = json.load(open("data/songs.json", "r"))
	root = Tk()
	root.withdraw()
	folder = filedialog.askdirectory()
	root.quit()

	for filename in os.listdir(folder):
		full_path = os.path.join(folder, filename)
		if filename.endswith((".mp3", ".wav", ".ogg")):
			if full_path not in data["songs"]:
				update_database(full_path.replace("\\", "/"))
				display_name = f"{ntpath.basename(filename)} [{format_length(full_path)}]"
				dpg.add_button(label=display_name, callback=play, width=-1, height=25,
							   user_data=full_path.replace("\\", "/"), parent="list")
				dpg.add_spacer(height=2, parent="list")

def search(sender, app_data, user_data):
	songs = json.load(open("data/songs.json", "r"))["songs"]
	dpg.delete_item("list", children_only=True)
	for index, song in enumerate(songs):
		if app_data in song.lower():
			dpg.add_button(label=f"{ntpath.basename(song)}", callback=play,width=-1, height=25, user_data=song, parent="list")
			dpg.add_spacer(height=2,parent="list")

def removeall():
	songs = json.load(open("data/songs.json", "r"))
	songs["songs"].clear()
	json.dump(songs,open("data/songs.json", "w"),indent=4)
	dpg.delete_item("list", children_only=True)
	load_database()

with dpg.theme(tag="base"):
	with dpg.theme_component():
		dpg.add_theme_color(dpg.mvThemeCol_Button, (30, 30, 30))
		dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (45, 45, 45))
		dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (60, 60, 60, 95))
		dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (15, 15, 15))
		dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (25, 25, 25))
		dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (45, 45, 45))
		dpg.add_theme_color(dpg.mvThemeCol_Border, (0, 0, 0, 0))
		dpg.add_theme_color(dpg.mvThemeCol_ScrollbarBg, (0, 0, 0, 0))
		dpg.add_theme_color(dpg.mvThemeCol_CheckMark, (180, 180, 180))
		dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 4)
		dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 5)
		dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 12, 16)

with dpg.theme(tag="slider_thin"):
	with dpg.theme_component():
		dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (40, 40, 40, 99))
		dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (50, 50, 50, 99))
		dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, (200, 200, 200))
		dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, (180, 180, 180))
		dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (35, 35, 35, 99))
		dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 3)
		dpg.add_theme_style(dpg.mvStyleVar_GrabMinSize, 30)

with dpg.theme(tag="slider"):
	with dpg.theme_component():
		dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (40, 40, 40, 99))
		dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (50, 50, 50, 99))
		dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, (200, 200, 200))
		dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, (180, 180, 180))
		dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (35, 35, 35, 99))
		dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 3)
		dpg.add_theme_style(dpg.mvStyleVar_GrabMinSize, 30)

with dpg.theme(tag="songs"):
	with dpg.theme_component():
		dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 2)
		dpg.add_theme_color(dpg.mvThemeCol_Button, (40, 40, 40, 40))
		dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (60, 60, 60, 70))
		
with dpg.font_registry():
	monobold = dpg.add_font("fonts/MonoLisa-Bold.ttf", 12)
	head = dpg.add_font("fonts/MonoLisa-Bold.ttf", 15)
	title = dpg.add_font("fonts/MonoLisa-Bold.ttf", 22)

with dpg.window(tag="main",label="window title"):
	with dpg.child_window(autosize_x=True,height=45,no_scrollbar=True):
		dpg.add_text(f"Now Playing : ",tag="csong")
	dpg.add_spacer(height=2)

	with dpg.group(horizontal=True):
		with dpg.group(horizontal=True):
			with dpg.child_window(width=250, tag="sidebar"):
				dpg.add_text("Rainy Musicart", tag="Rainy Musicart")
				dpg.bind_item_font("Rainy Musicart", title)

				dpg.add_text("Freddy-Edition", tag="Freddy-Edition")
				dpg.bind_item_font("Freddy-Edition", head)

				dpg.add_text("Build by NotCookey", tag="Build by NotCookey")

				dpg.add_text("&", tag="&")
				dpg.add_text("by Freddy-LVL9", tag="by Freddy-LVL9")

				dpg.add_spacer(height=2)
				dpg.add_button(label="Support", width=-1, height=23, callback=lambda: webbrowser.open("https://github.com/NotCookey/Rainy/issues"))
				dpg.add_spacer(height=5)
				dpg.add_separator()
				dpg.add_spacer(height=5)
				dpg.add_button(label="Add File",width=-1,height=28,callback=add_files)
				dpg.add_button(label="Add Folder",width=-1,height=28,callback=add_folder)
				dpg.add_button(label="Remove All Songs",width=-1,height=28,callback=removeall)
				dpg.add_spacer(height=5)
				dpg.add_separator()
				dpg.add_spacer(height=5)
				dpg.add_text(f"State: {state}",tag="cstate")
				dpg.add_spacer(height=5)
				dpg.add_separator()

		
		with dpg.child_window(autosize_x=True,border=False):
			with dpg.child_window(autosize_x=True,height=80,no_scrollbar=True):
				with dpg.group(horizontal=True):
					with dpg.group(horizontal=True):
						dpg.add_button(label="Play",width=65,height=30,tag="play",callback=play_pause)						
						dpg.add_button(label="Stop",callback=stop,width=65,height=30)
						dpg.add_button(label="Back",width=65,height=30,show=True,tag="pre",callback=pre)
						dpg.add_button(label="Next",tag="next",show=True,callback=next,width=65,height=30)
						dpg.add_text("0:00", tag="current_time")
						dpg.add_slider_float(tag="pos",format="",width=1000)
						dpg.add_text("0:00", tag="total_duration")
					dpg.add_slider_float(tag="volume", width=200, height=15,pos=(10,59), format="%.0f%%", default_value=_DEFAULT_MUSIC_VOLUME * 100, callback=update_volume)

						

			with dpg.child_window(autosize_x=True,delay_search=True):
				with dpg.group(horizontal=True,tag="query"):
					dpg.add_input_text(hint="Search for a song",width=-1,callback=search)
				dpg.add_spacer(height=5)
				with dpg.child_window(autosize_x=True,delay_search=True,tag="list"):
					load_database()

	dpg.bind_item_theme("volume","slider_thin")
	dpg.bind_item_theme("pos","slider")
	dpg.bind_item_theme("list","songs")

dpg.bind_theme("base")
dpg.bind_font(monobold)

def safe_exit():
	pygame.mixer.music.stop()
	pygame.quit()

atexit.register(safe_exit)

dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("main",True)
dpg.maximize_viewport()
dpg.start_dearpygui()
dpg.destroy_context()
