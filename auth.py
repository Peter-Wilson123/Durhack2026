import flask_login


class User(flask_login.UserMixin):
	def __init__(self, username, password):
		self.id = username
		self.password = password


users = {"test": User("test", "test")}


def register_user(username, password):
	users[username] = User(username, password)


def is_user(username):
	return username in users


def varify_user(username, password):
	if users[username].password == password:
		return users[username]


def get_user(username):
	return users[username]
