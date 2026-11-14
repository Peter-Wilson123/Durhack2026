import flask
import flask_login
import auth

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
    return """<form method="post">
      Username: <input name="username" required><br>
      Display Name: <input name="display_name" required><br>
      Email: <input name="email" type="email" required><br>
      Password: <input name="password" type="password" required><br>
      Bio: <textarea name="bio" rows="3" cols="30"></textarea><br>
      City: <input name="city"><br>
      Country: <input name="country"><br>
      Avatar URL (optional): <input name="avatar_url"><br>
      <button>Add account</button>
    </form>"""


@app.post("/register")
def register_post():
    username = flask.request.form.get("username", "").strip()
    display_name = flask.request.form.get("display_name", "").strip()
    email = flask.request.form.get("email", "").strip()
    password = flask.request.form.get("password", "")
    bio = flask.request.form.get("bio", "").strip()
    city = flask.request.form.get("city", "").strip()
    country = flask.request.form.get("country", "").strip()
    avatar_url = flask.request.form.get("avatar_url", "").strip()

    # Make sure required fields are filled and not already taken
    if not username or not display_name or not email or not password:
        return flask.redirect(flask.url_for("register"))

    if auth.is_user(username,email):
        return flask.redirect(flask.url_for("register"))

    auth.register_user(
        username=username,
        password=password,
        email=email,
        display_name=display_name,
        bio=bio,
        city=city,
        country=country,
        avatar_url=avatar_url,
    )
    return flask.redirect(flask.url_for("register_success"))


with app.app_context():
	db.create_all()


@app.route("/")
def home():
	return app.send_static_file("index.html")


if __name__ == "__main__":
	app.run("127.0.0.1", 5000)
