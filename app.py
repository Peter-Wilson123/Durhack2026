import flask
import flask_login
import auth

from models import (
	Category,
	ChatRoom,
	Connection,
	Interest,
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
def user_loader(user_id):
    return db.session.get(User, int(user_id))


with app.app_context():
    db.create_all()


@app.get("/account")
@flask_login.login_required
def account():
	return flask.render_template("account.html")


@app.get("/login")
def login_get():
    return flask.render_template("login.html")


@app.post("/login")
def login_post():
    login_input = flask.request.form.get("identifier", "").strip()
    password = flask.request.form.get("password", "")

    # Matches either username (CIS code) or email in the database
    user = auth.load_user(username=login_input, email=login_input, password=password)
    if not user:
        return flask.redirect(flask.url_for("login_get"))

    flask_login.login_user(user)
    return flask.redirect(flask.url_for("protected"))

@app.route("/logout")
def logout():
    flask_login.logout_user()
    return flask.redirect(flask.url_for("login_get"))


@app.route("/register_success")
def register_success():
	return """Successfully regiseterd"""


@app.get("/register")
def register():
	return flask.render_template("register.html")


@app.post("/register")
def register_post():
	username = flask.request.form.get("username", "").strip()
	email = flask.request.form.get("email", "").strip()
	password = flask.request.form.get("password", "")
	confirm_password = flask.request.form.get("confirm_password", "")

	# Make sure required fields are filled and not already taken
	if not username or not email or not password:
		return flask.redirect(flask.url_for("register"))

	if password != confirm_password:
		return flask.redirect(flask.url_for("register"))

	if auth.is_user(username, email):
		return flask.redirect(flask.url_for("register"))

	auth.register_user(
		username=username,
		email=email,
		password=password,

	)
	return flask.redirect(flask.url_for("register_success"))


with app.app_context():
	db.create_all()


@app.route("/")
def home():
	return flask.render_template("index.html")


if __name__ == "__main__":
	app.run("127.0.0.1", 5000)
