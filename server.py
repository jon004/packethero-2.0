# Main web app
# By Tanisha Babic
#-----------------------------------------------------------------------------#
import functools
from flask import Flask, render_template, session, request, flash, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, send, emit, disconnect, join_room, leave_room
from flask_login import UserMixin, login_user, login_required, current_user, logout_user
from forms import LoginForm
from apps import app, db, socketio, login_manager, Packets, Room
from models import User
import json
import datetime
import time
import math
#-----------------------------------------------------------------------------#


#----------------------------------------------------------------------------#
#-------------------------------game variables

login_manager.login_view = 'login'
packets = Packets() # scrambled packets for the game
rooms = {}
adminTokens = ['20foUWSN', '9AhXLJJB', 'kXsMmuID', 'iipcCtCw', 'BDqprSyj']

# session config
@app.before_request
def make_session_permanent():
	session.permanent = True

# Authentication method - if user is authenticated continue, else redirect to log in page
def authenticated_only(f):
	@functools.wraps(f)
	def wrapped(*args, **kwargs):
		if current_user.is_authenticated:
			return f(*args, **kwargs)
		else:
			return redirect(url_for('login'))
	return wrapped

#-----------------------------------------------------------------------------#
#-----------------------------------------------------------------------------#



#-----------------------------------------------------------------------------#
#----------------------------user events

# checks if all users in the team are ready
# - returns true if game is ready to start else false
def usersReady(id):
	user = User.query.filter_by(id=id).first() # current user
	# admins don't wait for a team, they play alone so their games are always ready
	if user.admin != 1:
		# list of users in team
		team = User.query.filter(User.teamname==user.teamname, User.song==user.song, User.room==user.room, User.admin==0, User.session!='n/a', User.id!=user.id).all()
		room_key = f'{user.teamname}_{user.song}_{user.room}_{user.admin}'
		if room_key in rooms:
			# list of users in team that ARE READY
			ready_users = rooms[room_key].getUsers()
			# iterates through team
			for u in team:
				# if a team member isn't in the list of users that ARE READY, the game is not ready to start
				if u.id not in ready_users:
					return False
		# if the game room doesn't exists, the game is not ready
		else:
			return False
	return True

# use to exit game
# note: not the same as logging out
def exitGame(id):
	user = User.query.filter_by(id=id).first()
	room_key = f'{user.teamname}_{user.song}_{user.room}_{user.admin}'
	# admmin keys include their username to make the keys unique because admins don't have teams
	if user.admin == 1:
		room_key = room_key + '_' + user.username
	# check if the user's room exists
	if room_key in rooms:
		# remove user from room
		rooms[room_key].removeUser(user.id)
		# if room empty after leaving the room, delete the room
		if rooms[room_key].empty():
			del rooms[room_key]
		# if the room is not empty check if the game is ready now that this user left
		else:
			# start game if users are all ready
			if usersReady(id):
				return startGame(id)

# Socket connection event
@socketio.on('connect')
@authenticated_only
def connect_handler():
	# join designated rooms
	join_room(current_user.room) # game room
	join_room(f'{current_user.teamname}_{current_user.room}_{current_user.admin}') # team chat
	if current_user.admin == 1: # admin room
		join_room('admins_' + current_user.room)
	elif current_user.song != '': # game room - only if a song has been selected (not for admins)
		room_key = f'{current_user.teamname}_{current_user.song}_{current_user.room}_{current_user.admin}'
		join_room(room_key)
	# set session id
	current_user.session = request.sid
	db.session.commit()

# Socket event to kick out a user
@socketio.on('kick-user')
@authenticated_only
def kick_user(username):
	# only admins can kick users so first we check if the user is admin
	if current_user.admin == 1:
		user = User.query.filter_by(username=username, room=current_user.room).first()
		# check if user exists
		if user != None:
			# logout the user
			socketio.emit('redirect', url_for('logout'), room=user.session)
			# if user was not redirected to logout successfully remove the user from database
			user = User.query.filter_by(username=username, room=current_user.room).first()
			if user != None:
				logoutUser(user.id)
		else:
			socketio.emit('send-msg', ['Server', 'User not found.'], room=request.sid)
	else:
		socketio.emit('send-msg', ['Server', 'Your account is not authorized to use /kick.'], room=request.sid)


# Returns a list of users. The user's username, teamname, songname, and status (idle/ready) are sent to the requester
@socketio.on('list-users')
@authenticated_only
def getUsers(team):
	# gathers our users data into a list
	users = []
	# gets users by teamname (admin only)
	if len(team) > 0 and current_user.admin == 1:
		matches = User.query.filter(User.teamname==team, User.room==current_user.room, User.admin==0, User.session != 'n/a').all()
	# gets ALL users in room (admin only)
	elif current_user.admin == 1:
		matches = User.query.filter(User.room==current_user.room, User.admin==0, User.session != 'n/a').all()
	# gets current user's team (student only)
	else:
		matches = User.query.filter(User.room==current_user.room, User.teamname==current_user.teamname, User.admin==0, User.session != 'n/a').all()
	# return formatted results to requester
	socketio.emit('send-msg', ['Server', ''], room=request.sid)
	socketio.emit('send-msg', ['', '-------------------------'], room=request.sid)
	socketio.emit('send-msg', ['','<username> : <teamname> : <song> : <status>'], room=request.sid)
	if matches != None and len(matches) > 0:
		for u in matches:
			room_key = f'{u.teamname}_{u.song}_{u.room}_{u.admin}'
			ready = 'ready' if (room_key in rooms and u.id in rooms[room_key].getUsers()) else 'idle'
			song = u.song if len(u.song) > 0 else 'none'
			socketio.emit('send-msg', ['', '------------------------------------'], room=request.sid)
			socketio.emit('send-msg', ['', f'{u.username} : {u.teamname} : {song} : {ready}'], room=request.sid)
		socketio.emit('send-msg', ['', '------------------------------------'], room=request.sid)
	else:
		socketio.emit('send-msg', ['','no users'], room=request.sid)

# update user status on disconnect
@socketio.on('disconnect')
@authenticated_only
def disconnect():
	# leave any joined rooms
	leave_room(current_user.room) # game room
	leave_room(f'{current_user.teamname}_{current_user.room}_{current_user.admin}') # team chat
	if current_user.admin == 1: # admin room
		leave_room('admins_' + current_user.room)
	elif current_user.song != '': # game room - only if a song has been selected (not for admins)
		room_key = f'{current_user.teamname}_{current_user.song}_{current_user.room}_{current_user.admin}'
		leave_room(room_key)
	# set session id to none
	current_user.session = 'n/a'
	db.session.commit()
#@socketio.on('pong-server')
#@authenticated_only
#def pong_server():
#	current_user.session = request.sid
#	db.session.commit()

#-----------------------------------------------------------------------------#
#-----------------------------------------------------------------------------#



#-----------------------------------------------------------------------------#
#---------------------------- SONG ROUTES

# Route to song if song exists, else redirect to song selection
@app.route("/song/<song_route>", methods=['GET', 'POST'])
@authenticated_only
def song(song_route):
	song_name = packets.routeToSong(song_route)
	# check if user in game to start game loop on load
	in_game = 0
	room_key = f'{current_user.teamname}_{current_user.song}_{current_user.room}_{current_user.admin}'
	if current_user.admin == 1:
		room_key = room_key + '_' + current_user.username
	if room_key in rooms and rooms[room_key].gameOver() == False and current_user.id in rooms[room_key].getUsers():
		in_game += 1
	# if there's an active song and this route is the active song -> render the page
	if in_game == 1 and current_user.song == song_name:
		return render_template(f'{song_route}.html', names=packets.getFrames(song_name), admin_flag=current_user.admin, song_choice=song_name, in_game=in_game, old_key='', admin=current_user.admin)
	# if there's an active song and the route doesn't match -> redirect to correct route
	elif in_game == 1 and current_user.song != song_name:
		return redirect('/song/' + packets.songToRoute(current_user.song))
	# if there's no active song and the song route is valid -> set the song and load page
	elif in_game == 0 and packets.validRoute(song_route):
		if len(current_user.song) > 0:
			old_key = room_key
			exitGame(id=current_user.id)
		else:
			old_key = ''
		current_user.song = song_name
		db.session.commit()
		return render_template(f'{song_route}.html', names=packets.getFrames(song_name), admin_flag=current_user.admin, song_choice=song_name, in_game=in_game, old_key=old_key, admin=current_user.admin)
	# else goto song selection page
	return redirect('/song')

# song selection screen
@app.route("/song", methods=["GET", "POST"])
@authenticated_only
def songSelect():
	room_key = f'{current_user.teamname}_{current_user.song}_{current_user.room}_{current_user.admin}'
	if current_user.admin == 1: # admin keys are slightly different
		room_key = room_key + '_' + current_user.username
	in_game = 0
	# checks if our room key is valid, if the game has started, and the current user is in that game
	if room_key in rooms and rooms[room_key].gameOver() == False and current_user.id in rooms[room_key].getUsers():
		in_game += 1
	return render_template('songs.html', in_game=in_game, admin=current_user.admin)

# redirects to /song incase user types the '/' at the end of the link
@app.route("/song/", methods=["GET", "POST"])
@authenticated_only
def songSelectB():
	return redirect('/song')

#-----------------------------------------------------------------------------#
#-----------------------------------------------------------------------------#



#-----------------------------------------------------------------------------#
#-------------------------------log in helpers

# logs out user by id (incase there are issues with redirecting to logout)
def logoutUser(id):
	user = User.query.filter_by(id=id).first()
	# check if the user exists
	if user != None:
		# broadcast to others that the user is leaving
		socketio.emit('send-msg', ['Server [All] ', f'{user.username} has left the room.', 0], broadcast=True, room=user.room)
		# leave a game the user was in it
		exitGame(id)
		# delete user from database
		User.query.filter_by(id=id).delete()
		db.session.commit()

#-------------------------------log in routes

@app.route("/", methods=['GET', 'POST'])
def loginRedirect():
	return redirect(url_for('login'))

# Loads log in page
# OR
# Retrieves form data, creates user session and adds user to db
@app.route("/login", methods=['GET', 'POST'])
def login():
	form = LoginForm()	# data has been through valid data checkers at this point (see forms.py)
	user = form.user.data
	team = form.team.data
	room = 'room'+str(form.room.data)
	# on form submission - create accounts, add them to database, and redirect to song page
	if form.validate_on_submit() and not current_user.is_authenticated:
		admin_flag = 1 if team in adminTokens else 0 # check if admin
		if admin_flag == 1:
			team = 'admins_' + room
		# delete user if already in database (to reset user values)
		player = User.query.filter_by(username=user, room=room).first()
		if player != None:
			User.query.filter_by(id=player.id).delete()
			db.session.commit()
		# create user, save user in DB, log in user, redirect
		player = User(username=user, teamname=team, room=room, admin=admin_flag, session='n/a', song='')
		db.session.add(player)
		db.session.commit()
		login_user(player)
		socketio.emit('send-msg', ['Server [All]', f'{user} has entered the room.', 0], broadcast=True, room=room)
		return redirect('song')
	elif current_user.is_authenticated:
		return redirect('song')
	# if form hasn't been submitted and no user is logged in -> load login screen
	return render_template('login.html', title='Login', form=form)

# logs out current user then redirects to log in
@app.route('/logout')
@authenticated_only
def logout():
	try:
		# broadcast to others that the user is leaving
		socketio.emit('send-msg', ['Server [All] ', f'{current_user.username} has left the room.', 0], broadcast=True, room=current_user.room)
		# leave a game the user was in it
		exitGame(current_user.id)
		# delete user from database
		User.query.filter_by(id=current_user.id).delete()
		db.session.commit()
	except:
		print('already removed')
	# redirect user to login page
	return redirect(url_for('login'))

#-----------------------------------------------------------------------------#
#-----------------------------------------------------------------------------#



#-----------------------------------------------------------------------------#
#------------------------------Game

# request to see the selected song
@socketio.on('request-song')
@authenticated_only
def requestSong():
	msg = f'Your selected song is {current_user.song}.' if current_user.song != '' else 'Select a song'
	return socketio.emit('send-msg', ['Server', msg, 0], room=request.sid)

# used to leave a game room that has ended
@socketio.on('disconnect-room')
@authenticated_only
def disconnectRoom():
	room_key = f'{current_user.teamname}_{current_user.song}_{current_user.room}_{current_user.admin}_ready'
	if current_user.admin == 1:
		room_key = f'{current_user.teamname}_{current_user.song}_{current_user.room}_{current_user.admin}_{current_user.username}_ready'
	leave_room(room_key)

#------------------------------

# starts game of a user (game room found using the user's id)
def startGame(id):
	user = User.query.filter_by(id=id).first()
	room_key = f'{user.teamname}_{user.song}_{user.room}_{user.admin}'
	if user.admin == 1: # admin keys are slightly different than student keys
		room_key = room_key + '_' + user.username
	rooms[room_key].start()
	time = rooms[room_key].secondsLeft()
	# start message is slightly different for admins
	if user.admin == 0:
		socketio.emit('send-msg', ['Server [Team]', 'Your team is ready! The game will start in 5 seconds. You will have 10 seconds to submit frame 1.', 0], broadcast=True, room=room_key + '_ready')
	else:
		socketio.emit('send-msg', ['Server [Team]', 'Your game will start in 5 seconds. You will have 10 seconds to submit frame 1.', 0], broadcast=True, room=room_key + '_ready')
	# starts game loop (client-side)
	socketio.emit('game-loop', time, room=room_key + '_ready')
	# initializes game variables
	rooms[room_key].start()

#-----------------------------------------------------------------------------#

# sends /admin messages
def sendAdminMsg(msg):
	if current_user.admin != 1:
		sender = f'{current_user.username} [to:admins] [{current_user.teamname}]'
		room_key = 'admins_' + current_user.room
		socketio.emit('send-msg', [sender, msg, 4], room=request.sid)
		socketio.emit('send-msg', [sender, msg, 4], room=room_key)

# sends /team messages
def sendTeamMsg(msg):
	sender = f'{current_user.username} [team] [admin]' if current_user.admin == 1 else f'{current_user.username} [team] [{current_user.teamname}]'
	room_key = 'admins_' + current_user.room if current_user.admin == 1 else f'{current_user.teamname}_{current_user.room}_{current_user.admin}'
	color_flag = 3 if current_user.admin != 1 else 1
	# all team messages are sent to admins so they can moderate chat
	socketio.emit('send-msg', [sender, msg, color_flag], room=f'admins_{current_user.room}')
	# only send message here if user is not admin because it was already sent to admin (in the line of code above this comment)
	if current_user.admin != 1:
		socketio.emit('send-msg', [sender, msg, color_flag], room=room_key)

# sends /all messages
def sendAllMsg(msg):
	room_key = current_user.room if current_user.admin == 1 else request.sid
	sender = f'{current_user.username} [all]' if current_user.admin == 1 else 'Server'
	msg = msg if current_user.admin == 1 else 'Your account is not authorized to send /all messages.'
	color_flag = 1 if current_user.admin == 1 else 0
	socketio.emit('send-msg', [sender, msg, color_flag], room=room_key)

# sends /private messages
# note: private messages should look like...
# msg = "<username> <message>"
def sendPrivateMessage(msg):
	# only admins can send private messages
	if current_user.admin != 1:
		return socketio.emit('send-msg', ['Server', 'Your account is not authorized to send /private messages.'], room=request.sid)
	# checks if msg is parsable
	if len(msg.split(' ')) > 1:
		reciever = msg[:msg.index(' ')].strip()
		sender = f'{current_user.username} [private] [{reciever}]'
		msg = msg[msg.index(' '):].strip()
		# get the reciever's data and see if the user exists to get their session id
		user = User.query.filter_by(username=reciever, room=current_user.room).first()
		if user != None and user.session != 'n/a':
			socketio.emit('send-msg', [sender, msg, 1], room=f'admins_{current_user.room}')
			return socketio.emit('send-msg', [sender, msg, 1], room=user.session)
		else:
			return socketio.emit('send-msg', ['Server', f'"{reciever}" was not found.'], room=request.sid)
	return socketio.emit('send-msg', ['Server', 'Your message is missing.'], room=request.sid)


# sends messages
@socketio.on('send-msg')
@authenticated_only
def teamMsg(to, msg):
	if to == '/admin':
		sendAdminMsg(msg)
	elif to == '/team':
		sendTeamMsg(msg)
	elif to == '/all':
		sendAllMsg(msg)
	elif to == '/private':
		sendPrivateMessage(msg)
	else:
		socketio.emit('send-msg', ['Server', 'Something went wrong. Your message was not sent. Try again.'], room=request.sid)

# handle's user's answer attempts
@socketio.on('input-frame')
@authenticated_only
def inputFrame(frame):
	room_key = f'{current_user.teamname}_{current_user.song}_{current_user.room}_{current_user.admin}'
	if current_user.admin == 1:
		room_key = room_key + '_' + current_user.username
	if room_key in rooms and rooms[room_key].gameOver() == False and rooms[room_key].secondsLeft() > 0:
		room = rooms[room_key]
		# returns true if correct else returns hint
		correct = room.checkFrame(frame)
		won = room.won()
		if correct:
			# if won then game's over
			if won:
				msg = 'Congratulations! Your team loaded the song! GAME OVER'
				socketio.emit('send-msg', ['Server [Team]', msg, 0], room=room_key)
			# onto the next frame if frame is correct
			else:
				msg = f'Good job! You have 10 seconds to send frame {room.current_frame}.'
				socketio.emit('send-msg', ['Server [Team]', msg, 0], room=room_key + '_ready')
		else:
			# game over if frame incorrect
			msg = f'{current_user.username} submitted the wrong frame GAME OVER [input({frame}) - {correct}]'
			socketio.emit('send-msg', ['Server [Team]', msg, 0], room=room_key + '_ready')
			del rooms[room_key]
		# ends game loop if won or lost
		if won:
			socketio.emit('close-loop', win=True, room=room_key + '_ready')
		elif not correct:
			socketio.emit('close-loop', win=False, room=room_key + '_ready')

# game loop reports game status to players
@socketio.on('game-loop')
@authenticated_only
def gameStats():
	room_key = f'{current_user.teamname}_{current_user.song}_{current_user.room}_{current_user.admin}'
	if current_user.admin == 1:
		room_key = room_key + '_' + current_user.username
	if room_key in rooms:
		room = rooms[room_key]
		time = int(room.secondsLeft())
		# game end cases
		if room.gameOver():
			win = False
			# time updates for gamers
			if time == 0:
				socketio.emit('send-msg', ['Time', 0, 2], room=request.sid)
				socketio.emit('send-msg', ['Server [Team]', 'Your team ran out of time GAME OVER.', 0], room=request.sid)
			elif room.won():
				win=True
			socketio.emit('close-loop', win=win, room=request.sid)
			room.removeUser(current_user.id)
			# delete room when empty
			if room.empty():
				# broadcast win message to EVERYONE
				if room.won():
					socketio.emit('send-msg', ['Server [All]', f'Team {current_user.teamname} successfully loaded "{current_user.song}"!'], broadcast=True, room=current_user.room)
				# delete room once it's empty
				del rooms[room_key]
		# continues game
		else:
			socketio.emit('game-loop', time, request.sid)
	else:
		socketio.emit('close-loop', request.sid)

# starts game if team is ready
@socketio.on('ready')
@authenticated_only
def ready():
	if current_user.song != '':
		room_key = f'{current_user.teamname}_{current_user.song}_{current_user.room}_{current_user.admin}'
		if current_user.admin == 1:
			room_key = room_key + '_' + current_user.username
		# create game room if it doesn't exist yet
		if room_key not in rooms:
			rooms[room_key] = Room(packets.getFrames(current_user.song))
		# if user hasn't joined
		if current_user.id not in rooms[room_key].getUsers():
			# try to add user to room
			added = rooms[room_key].addUser(current_user.id)
			# this is the case when the game has already started (can't join ongoing game)
			if not added:
				return socketio.emit('send-msg', ['Server', 'This game has already started. Try again later or pick another song.'], room=request.sid)
			if added:
				# add user to game
				join_room(room_key + '_ready')
				socketio.emit('send-msg', ['Server [Team]', f'{current_user.username} is ready', 0], broadcast=True, room=room_key)
				# if all users ready start the game
				if usersReady(current_user.id):
					return startGame(current_user.id)
				else:
					return socketio.emit('send-msg', ['Server', 'Waiting for players...', 0], room=request.sid)
		else:
			# print message if already waiting
			allready = usersReady(current_user.id)
			if not allready:
				return socketio.emit('send-msg', ['Server', 'Waiting for players...', 0], room=request.sid)
			# start the game if everyone is ready and the game hasn't started
			if allready and rooms[room_key].gameOver() == True:
				return startGame(current_user.id)
	else:
		return socketio.emit('send-msg', ['Server', 'You haven\'t selected a song', 0], room=request.sid)

#-----------------------------------------------------------------------------#
#-----------------------------------------------------------------------------#

# Run app
# Uncomment when running locally
if __name__ == '__main__':
	socketio.run(app, host='0.0.0.0', port='5000', debug=True)

#-----------------------------------------------------------------------------#
#-----------------------------------------------------------------------------#
