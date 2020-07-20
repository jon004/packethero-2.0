# Team sign up form with valid input checkers
# By Tanisha Babic
#-----------------------------------------------------------------------------#
from flask import current_app
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError
from models import User
from apps import db, socketio
# from profanity_check import predict, predict_prob
import string
#-----------------------------------------------------------------------------#

# used in validate_user function to access data gathered in validate_team & validate_room functions
# IFF the values are pass validation checks
class Validator_Helper():
	def __init__(self, team_val, room_val):
		self.team_val = team_val
		self.room_val = room_val

# Validator_Helper initiated with null equivalent values ('temp')
helper = Validator_Helper('temp', 'temp')

#-----------------------------------------------------------------------------#
#--------------------------validate checkers

# checks if username is taken or has special characters
def validate_user(form, user):
	# # valid input check 0: Profanity check - has raised false flags so it's commented out for now
	# prof = predict_prob([user.data])
	# if (prof[0] > 0.5):
	# 	raise ValidationError('Profanity detected. Try again.')
	if len(user.data) > 36:
		raise ValidationError('Username too long')
	# valid input check 1: no special characters allowed
	for char in user.data:
		if (char in string.punctuation) or (char == " "):
			raise ValidationError('Enter an appropriate username (no special characters allowed)')
	# valid input check 2: (DB query check) checks if there's an active user with the requested username
	player = db.session.query(User).filter(User.username == user.data, User.room == 'room' + str(helper.room_val)).first()
	if player != None and player.session != 'n/a': # admins may log in to multiple computers simultaneusly
	#	sid = player.session
	#	player.session = 'n/a'
	#	db.session.commit()
	#	#socketio.emit('ping-user', room=sid)
		raise ValidationError('This username is taken')
	elif player != None and player.session == 'n/a':
		User.query.filter_by(id=player.id).delete()
		db.session.commit()

# checks if teamname has special characters
def validate_team(form, team):
	# # valid input check 0: Profanity check - has raised false flags so it's commented out for now
	# prof = predict_prob([team.data])
	# if (prof[0] > 0.5):
	# 	raise ValidationError('Profanity detected. Try again.')

	# valid input check: no special characters allowed
	if len(team.data) > 36:
		raise ValidationError('Teamname too long')
	for char in team.data:
		if (char in string.punctuation) or (char == " "):
			raise ValidationError('Enter an appropriate team name (no special characters allowed)')
	if team.data.lower() == "admin" or team.data.lower() == "admins":
		raise ValidationError('Teamname can\'t be "admin"')
	# if no validationErrors -> helper.team_val = teamname
	helper.team_val = team.data


# checks if roomname is an integer and if
def validate_room(form, room):
	# valid input check 1: try/catch: incase of bad input
	try:
		room = int(room.data)
	except Exception as e:
		raise ValidationError("Enter an appropriate room number.")
	# valid input check 2: floats and negatives not allowed, neither are numbers > 16
	if (room < 1) or  not float(room).is_integer() or (room > 16):
		raise ValidationError("Enter an appropriate room number.")
	# if no validationErrors -> helper.room_val = room
	helper.room_val = room

#-----------------------------------------------------------------------------#
#-----------------------------------------------------------------------------#


# Main - the actual form
# This stores a user's form input if all valitation checkers are passed
# If an input is invalid the user will be notified and the form will not go through until it passes
class LoginForm(FlaskForm):
	# The code below is equivalent to... <input type='text' name='Team Name' pattern='**' required/>
	#	**some regex pattern that takes care of valid input (ex: a regex pattern that filter out special characters)
	# The value is stored as the variable team in our class/object
	team = StringField('Team Name', validators=[DataRequired(), validate_team])
	room = StringField('Room Number', validators=[DataRequired(), validate_room])
	user = StringField('User Name', validators=[DataRequired(), validate_user])
	submit = SubmitField('Log in.')
