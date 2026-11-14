import flask_login
from sqlalchemy import or_
from models import User, db


from sqlalchemy import func
from models import User, db

def load_user(
    username: str = "",
    email: str = "",
    password: str = "",
) -> User | None:
    """
    Looks up a user by username or email and verifies their password.
    Returns the User object if valid, or None if not found / wrong password.
    """
    if not password:
        return None

    clean_username = (username or "").strip().lower()
    clean_email = (email or "").strip().lower()

    conditions = []
    if clean_username:
        conditions.append(User.username == clean_username)
    if clean_email:
        conditions.append(User.email == clean_email)

    if not conditions:
        return None

    user = User.query.filter(or_(*conditions)).first()

    if user and user.check_password(password):
        return user

    return None

def register_user(username: str, email: str, password: str) -> User:
	"""Creates a new User row in SQLite using the user's form inputs."""
	clean_username = username.strip().lower()
	clean_email = email.strip().lower()

	new_user = User(username=clean_username, email=clean_email)
	new_user.set_password(password)

	db.session.add(new_user)
	db.session.commit()
	return new_user


def is_user(email: str, username: str = "") -> bool:
	"""Returns True if an account already exists with this email or username."""
	clean_email = (email or "").strip().lower()
	clean_username = (username or "").strip().lower()

	conditions = []
	if clean_email:
		conditions.append(User.email == clean_email)
		# Also check against username if only one argument was passed
		if not clean_username:
			conditions.append(User.username == clean_email)
	if clean_username:
		conditions.append(User.username == clean_username)

	if not conditions:
		return False

	return User.query.filter(or_(*conditions)).first() is not None
