import flask
import flask_login


from models import (
	Category,
	ChatRoom,
	Connection,
	Interest,
	Location,
	RoomMessage,
	User,
	UserInterest,
	db,
)

app = flask.Flask(__name__)
app.config["SECRET_KEY"] = "change-this-hackathon-secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


login_manager = flask_login.LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
	return db.session.get(User, int(user_id))


@login_manager.unauthorized_handler
def unauthorized():
	return flask.jsonify({"error": "Authentication required"}), 401


with app.app_context():
	db.create_all()


@app.get("/login")
def login_get():
	return """<form method=post>
	  Email: <input name="email"><br>
	  Password: <input name="password" type=password><br>
	  <button>Log In</button>
	</form>"""


@app.post("/login")
def login_post():
	username = flask.request.form["email"]
	password = flask.request.form["password"]

	if username is None or not auth.varify_user(username, password):
		return flask.redirect(flask.url_for("login_get"))

	flask_login.login_user(auth.get_user(username))
	return flask.redirect(flask.url_for("protected"))


@app.route("/protected")
@flask_login.login_required
def protected():
	return flask.render_template_string(
            "Logged in as: {{ user.id }}",
            user=flask_login.current_user
        )


@app.route("/logout")
def logout():
	flask_login.logout_user()
	return "Logged out"


@app.route("/register_success")
def register_success():
	return """Successfully regiseterd"""


@app.get("/register")
def register():
	return """<form method=post>
	  Email: <input name="email"><br>
	  Password: <input name="password" type=password><br>
	  <button>Add account</button>
	</form>"""


@app.post("/register")
def register_post():
	username = flask.request.form["email"]
	password = flask.request.form["password"]

	if username is None or not auth.is_user(username):
		print("true")
		flask.redirect(flask.url_for("register"))

	auth.register_user(username, password)
	return flask.redirect(flask.url_for("register_success"))


with app.app_context():
	db.create_all()


@app.route("/")
def home():
	return app.send_static_file("index.html")


if __name__ == "__main__":
	app.run("127.0.0.1", 5000)
