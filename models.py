# DataBase management
# by Tanisha Babic
#-----------------------------------------------------------------------------#
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from flask_login import LoginManager, UserMixin
from apps import db, login_manager
#-----------------------------------------------------------------------------#

# retrieves user data from database
@login_manager.user_loader
def load_user(user_id):
	try:
		int_val = int(user_id)
		return User.query.get(int(user_id))
	except:
		print('Failure')
		return None


# model for Database Table
# a column represents a unique accountZzz
class User(db.Model, UserMixin):
	__tablename__ = 'gamers'
	id = db.Column(Integer(), primary_key=True, unique=True, autoincrement=True)
	username = db.Column(String(200), nullable=False, unique=False)
	teamname = db.Column(String(200), nullable=False, unique=False)
	room = db.Column(String(200), nullable=False, unique=False)
	admin = db.Column(Integer(), unique=False, nullable=False)
	session = db.Column(String(200), unique=False, nullable=False)
	song = db.Column(String(200), unique=False, nullable=False)

	def __repr__(self):
		return f"User('{self.teamname}', '{self.username}', '{self.admin}', '{self.room}', '{self.session}')"
