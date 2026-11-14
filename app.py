from flask import Flask, jsonify, request
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from sqlalchemy import func, or_

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

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-hackathon-secret"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({"error": "Authentication required"}), 401


with app.app_context():
    db.create_all()

@app.route("/")
def hello_world():
	return app.send_static_file("index.html")


if __name__ == "__main__":
	app.run("127.0.0.1", 5000)
