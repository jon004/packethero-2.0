# Flask socketio emit fix
import eventlet
eventlet.monkey_patch() # eventlet patch

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_login import LoginManager
from random import randint
import time

# DB Variables
username = ''
passw = ''
host = ''
database = ''
port = ''
SECRET_KEY=''

app = Flask(__name__, static_url_path='/', static_folder='web/public', template_folder='web/templates')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI']= f'mysql+pymysql://{username}:{passw}@{host}:{port}/{database}'
db = SQLAlchemy(app)

socketio = SocketIO(app, cors_allowed_origins='*')
login_manager = LoginManager(app)

def getPackets(length):
	packets = []
	letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
		'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V',
		'W', 'X', 'Y', 'Z']
	i = 0
	while i < length:
		packet = str(randint(0, 9)) + letters[randint(0,25)] + str(randint(0,9)) + letters[randint(0,25)]
		if packet not in packets:
			packets.append(packet)
			i += 1
	return packets


class Packets:
	def __init__(self):
		self.africa = getPackets(29)
		self.bob = getPackets(29)
		self.cups = getPackets(13)
		self.journey = getPackets(25)
		self.smash = getPackets(20)

	def getFrames(self, x=''):
		route = self.songToRoute(x)
		if route == 'africa':
			return self.africa
		elif route == 'journey':
			return self.journey
		elif route == "bob":
			return self.bob
		elif route == 'cups':
			return self.cups
		elif route == 'smash':
			return self.smash
		return {} # in not found

	def validSong(self, x=''):
		songs = ['Africa', "Don't Stop Believing", "Don't Worry Be Happy", 'Cups', 'Allstar']
		if x in songs:
			return True
		return False

	def validRoute(self, x=''):
		routes = ['cups', 'smash', 'journey', 'bob', 'africa']
		if x in routes:
			return True
		return False

	def songToRoute(self, x=''):
		songData = { 'Cups': 'cups', 'Allstar': 'smash', "Don't Stop Believing": "journey", "Don't Worry Be Happy": "bob", 'Africa': 'africa' }
		if x in songData:
			return songData[x]
		if self.validRoute(x):
			return x
		return ''

	def routeToSong(self, x=''):
		songData = { 'cups': 'Cups', 'smash': 'Allstar', 'journey': "Don't Stop Believing", 'bob': "Don't Worry Be Happy", 'africa': 'Africa' }
		if x in songData:
			return songData[x]
		if self.validSong(x):
			return x
		return ''

class Room:
	def __init__(self, packets):
		self.start_time = -1
		self.current_frame = 1
		self.frames = packets
		self.ready_users = []

	def won(self):
		if len(self.frames) < self.current_frame:
			return True
		return False

	def start(self):
		self.start_time = time.time() + 5
		self.current_frame = 1

	# a player has 10 total seconds, this tells us how many are left
	def secondsLeft(self):
		# this checks if the game has started, the game officially starts 5 seconds after using start()
		if time.time() < self.start_time:
			return -1
		# if start_time is negative or seconds left is negative return 0
		seconds = int(11 - (time.time() - self.start_time) % 60)
		if self.start_time < 0 or seconds <= 0 or self.won():
			return 0
		# if the time left is positive that's how much time is left
		return seconds

	def gameOver(self):
		# if time's up and game hasn't closed, end it
		if self.won() or self.secondsLeft() == 0:
			return True
		return False

	def checkFrame(self, frame=''):
		# if game's over all frames are false
		frames = self.frames
		if self.gameOver():
			return False
		# if entered frame doesn't match our current frame start over
		if frame != frames[self.current_frame - 1]:
			self.start_time -= 10000
			if frame in frames:
				index = frames.index(frame) + 1
				if index > self.current_frame:
					return 'hint: this frame comes later'
				if index < self.current_frame:
					return 'hint:this frame was already sent'
			else:
				return "hint: this frame doesn't exist"
		self.current_frame += 1
		self.start_time = time.time()
		return True

	def getUsers(self):
		return self.ready_users

	def addUser(self, user):
		if self.gameOver():
			if user not in self.ready_users:
				self.ready_users.append(user)
			return True # return true if user was added
		return False # return false if not, users cant join after game starts

	def removeUser(self, user):
		if user in self.ready_users:
			self.ready_users.remove(user)

	def empty(self):
		if len(self.ready_users) == 0:
			return True
		return False
