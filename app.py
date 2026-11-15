import os
import flask
import flask_login
from werkzeug.middleware.proxy_fix import ProxyFix

import auth
import discovery
import find_new_interest
import interests
import profiles
import user_account
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

# Trust Azure's reverse-proxy headers so HTTPS and redirects work properly
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

is_azure = bool(os.environ.get("WEBSITE_SITE_NAME"))

app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "change-this-hackathon-secret"
)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
if is_azure:
    app.config["SESSION_COOKIE_SECURE"] = True

# Use Azure PostgreSQL when DATABASE_URL is set; fall back to SQLite locally
database_url = os.environ.get("DATABASE_URL", "").strip()
if database_url:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }
elif is_azure:
    os.makedirs("/home/data", exist_ok=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////home/data/app.db"
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = flask_login.LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def user_loader(user_id):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None


@login_manager.unauthorized_handler
def unauthorized():
    return flask.render_template("unauthorized.html")


with app.app_context():
    db.create_all()

interests.init_app(app)
profiles.init_app(app)


@app.get("/account")
@flask_login.login_required
def account():
    return flask.render_template("account.html")


@app.get("/login")
def login_get():
    return flask.render_template("login.html")


@app.post("/login")
def login_post():
    identifier = flask.request.form.get("identifier", "").strip()
    password = flask.request.form.get("password", "")
    user = auth.verify_user(
        username=identifier, email=identifier, password=password
    )
    if not user:
        return flask.redirect(flask.url_for("login_get"))
    flask_login.login_user(user)
    return flask.redirect(flask.url_for("home"))


@app.route("/logout")
def logout():
    flask_login.logout_user()
    return flask.redirect(flask.url_for("login_get"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if flask.request.method == "POST":
        username = flask.request.form.get("username", "").strip()
        email = flask.request.form.get("email", "").strip()
        password = flask.request.form.get("password", "")
        confirm_password = flask.request.form.get("confirm_password", "")

        if not username or not email or not password:
            return flask.render_template("register.html")
        if password != confirm_password:
            return flask.render_template("register.html")

        if not email.lower().endswith("@durham.ac.uk"):
            return flask.render_template(
                "register.html",
                error="This site is for Durham students only. Please use your student @durham.ac.uk address.",
            )

        if auth.is_user(email, username):
            return flask.render_template("register.html")

        auth.register_user(
            username=username,
            email=email,
            password=password,
        )
        user = auth.load_user(username=username, email=email)
        flask_login.login_user(user)
        return flask.render_template("success.html")
    return flask.render_template("register.html")


@app.post("/update-account")
@flask_login.login_required
def update_account():
    user_account.update_user_account(
        user=flask_login.current_user,
        new_username=flask.request.form.get("new-username", ""),
        new_bio=flask.request.form.get("new-bio", ""),
        new_interests=flask.request.form.get("new-interests", ""),
        remove_interests=flask.request.form.get("remove-interests", ""),
    )
    return flask.redirect(flask.url_for("account"))


@app.get("/find-new-interest")
@flask_login.login_required
def discover_new_interest():
    recommended = find_new_interest.find_new_interest(flask_login.current_user)
    if recommended:
        return flask.redirect(
            flask.url_for(
                "interests.view_interest",
                interest_id=recommended.interest_id,
            )
        )
    return flask.redirect(flask.url_for("account"))


@app.route("/")
def home():
    return flask.render_template(
        "index.html", chips=discovery.suggested_names(16)
    )


if __name__ == "__main__":
    app.run("127.0.0.1", 5000)