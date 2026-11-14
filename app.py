import flask
import flask_login
import auth
import discovery
import interests
import search
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
	return db.session.get(User, user_id)


@login_manager.unauthorized_handler
def unauthorized():
	return flask.render_template("unauthorized.html")


with app.app_context():
	db.create_all()

# Interest discovery, tags and interest pages (see interests.py)
interests.init_app(app)


@app.get("/account")
@flask_login.login_required
def account():
	return flask.render_template("account.html")


# LOGIN #

@app.get("/login")
def login_get():
	return flask.render_template("login.html")


@app.post("/login")
def login_post():
	login_input = flask.request.form.get("identifier", "").strip()
	password = flask.request.form.get("password", "")

	# Matches either username (CIS code) or email in the database
	user = auth.load_user(username=login_input,
                       email=login_input, password=password)
	if not user:
		return flask.redirect(flask.url_for("login_get"))

	flask_login.login_user(user)
	return flask.redirect(flask.url_for("account"))


@app.route("/logout")
def logout():
	flask_login.logout_user()
	return flask.redirect(flask.url_for("login_get"))


@app.route("/register_success")
def register_success():
	return """Successfully regiseterd"""


@app.route("/register", methods=["GET", "POST"])
def register():
	if flask.request.method == "POST":
		username = flask.request.form.get("username", "").strip()
		email = flask.request.form.get("email", "").strip()
		password = flask.request.form.get("password", "")
		confirm_password = flask.request.form.get("confirm_password", "")

		# Make sure required fields are filled and not already taken
		if not username or not email or not password:
			return flask.render_template("register.html")

		if password != confirm_password:
			return flask.render_template("register.html")

		if auth.is_user(username, email):
			return flask.render_template("register.html")

		auth.register_user(
			username=username,
			email=email,
			password=password,

		)
		return flask.redirect(flask.url_for("register_success"))

	return flask.render_template("register.html")


@app.route("/search", methods=["GET", "POST"])
def search_getpost():

	results = []
	search_term = ""

	if flask.request.method == "POST":

		search_term = flask.request.form.get("search", "").strip()

	exclude_id = (
            flask_login.current_user.user_id
            if flask_login.current_user.is_authenticated
            else None
        )
	users = search.find_users_by_interest(
            search_term, exclude_user_id=exclude_id)
	print(users)
	return flask.render_template(
            "search.html",
            results=users,
            search_term=search_term
	)


with app.app_context():
	db.create_all()


@app.route("/")
def home():
	return flask.render_template("index.html", chips=discovery.suggested_names(16))


if __name__ == "__main__":
	app.run("127.0.0.1", 5000)
