import flask_login


class User(flask_login.UserMixin):
	def __init__(self, email, password):
		self.id = email
		self.password = password


users = {"test": User("test", "test")}


def register_user(username, password):
	pass


def varify_user(username, password):
	if users[username].password == password:
		return users[username]


def get_user(username):
	return users[username]
