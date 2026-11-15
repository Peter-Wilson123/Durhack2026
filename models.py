from datetime import datetime, timezone
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


def utc_now():
	return datetime.now(timezone.utc)


# User class will be used to interact with the database and the website


class User(UserMixin, db.Model):
	__tablename__ = "users"

	user_id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(50), unique=True, nullable=False)
	display_name = db.Column(db.String(100), nullable=True)
	email = db.Column(db.String(120), unique=True, nullable=False)
	password_hash = db.Column(db.String(256), nullable=False)
	year = db.Column(db.String(30), nullable=True)
	show_year = db.Column(db.Boolean, default=False, nullable=False)
	avatar_colour = db.Column(db.String(30), default="palatinate", nullable=False)
	bio = db.Column(db.Text, default="")
	bio_published = db.Column(db.Boolean, default=False, nullable=False)
	avatar_url = db.Column(db.String(255), default="")

    # Connection-only contact details
	contact_instagram = db.Column(db.String(60), default="")
	contact_x = db.Column(db.String(60), default="")
	contact_email = db.Column(db.String(120), default="")

	created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
	# Relationships
	user_interests = db.relationship(
		"UserInterest", back_populates="user", cascade="all, delete-orphan"
	)
	created_interests = db.relationship(
		"Interest", back_populates="creator"
	)
	administered_rooms = db.relationship(
		"ChatRoom", back_populates="admin"
	)
	room_messages = db.relationship(
		"RoomMessage", back_populates="author"
	)

	# Self-referential / dual-FK relationships
	sent_connections = db.relationship(
		"Connection",
		foreign_keys="Connection.requester_id",
		back_populates="requester",
		cascade="all, delete-orphan",
	)
	received_connections = db.relationship(
		"Connection",
		foreign_keys="Connection.addressee_id",
		back_populates="addressee",
		cascade="all, delete-orphan",
	)
	sent_messages = db.relationship(
		"DirectMessage",
		foreign_keys="DirectMessage.sender_id",
		back_populates="sender",
	)
	received_messages = db.relationship(
		"DirectMessage",
		foreign_keys="DirectMessage.receiver_id",
		back_populates="receiver",
	)

	# Required by Flask-Login since PK is user_id instead of id
	def get_id(self):
		return str(self.user_id)

	def set_password(self, password: str):
		self.password_hash = generate_password_hash(password)

	def check_password(self, password: str) -> bool:
		return check_password_hash(self.password_hash, password)


# Category -> Tags -> Interests
# A tag can sit in several categories, and an interest can have any number of
# tags (including none). Interests reach categories only through their tags.

tag_categories = db.Table(
	"tag_categories",
	db.Column("tag_id", db.Integer, db.ForeignKey(
		"tags.tag_id"), primary_key=True),
	db.Column(
		"category_id", db.Integer, db.ForeignKey("categories.category_id"), primary_key=True
	),
)

interest_tags = db.Table(
	"interest_tags",
	db.Column(
		"interest_id", db.Integer, db.ForeignKey("interests.interest_id"), primary_key=True
	),
	db.Column("tag_id", db.Integer, db.ForeignKey(
		"tags.tag_id"), primary_key=True),
)


class Category(db.Model):
	"""Broad, curated field of knowledge or activity. Managed by seed data, not users."""

	__tablename__ = "categories"

	category_id = db.Column(db.Integer, primary_key=True)
	category_name = db.Column(db.String(100), unique=True, nullable=False)
	description = db.Column(db.Text, default="")

	tags = db.relationship("Tag", secondary=tag_categories,
	                       back_populates="categories")

	@property
	def interests(self):
		"""Interests reached through this category's tags."""
		seen = {}
		for tag in self.tags:
			for interest in tag.interests:
				seen[interest.interest_id] = interest
		return list(seen.values())


class Tag(db.Model):
	"""Specific, user-extensible descriptor such as "telescopes" or "hema"."""

	__tablename__ = "tags"

	tag_id = db.Column(db.Integer, primary_key=True)
	# Stored normalised: lower case, single spaces (see normalise_tag)
	tag_name = db.Column(db.String(40), unique=True, nullable=False)
	created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

	categories = db.relationship(
		"Category", secondary=tag_categories, back_populates="tags"
	)
	interests = db.relationship(
		"Interest", secondary=interest_tags, back_populates="tags"
	)


def normalise_tag(name: str) -> str:
	return " ".join((name or "").strip().lower().lstrip("#").split())[:40]


class Interest(db.Model):
	__tablename__ = "interests"

	interest_id = db.Column(db.Integer, primary_key=True)
	interest_name = db.Column(db.String(120), unique=True, nullable=False)
	description = db.Column(db.Text, default="")
	cover_image_url = db.Column(db.String(255), default="")
	# NULL = system-seeded interest; populated = user-created interest
	created_by_user_id = db.Column(
		db.Integer, db.ForeignKey("users.user_id"), nullable=True
	)
	created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

	tags = db.relationship(
		"Tag", secondary=interest_tags, back_populates="interests", order_by="Tag.tag_name"
	)
	creator = db.relationship("User", back_populates="created_interests")
	user_interests = db.relationship(
		"UserInterest", back_populates="interest", cascade="all, delete-orphan"
	)
	chat_room = db.relationship(
		"ChatRoom",
		back_populates="interest",
		uselist=False,
		cascade="all, delete-orphan",
	)

	@property
	def categories(self):
		"""Categories reached through this interest's tags, most common first."""
		counts = {}
		for tag in self.tags:
			for cat in tag.categories:
				counts[cat] = counts.get(cat, 0) + 1
		return sorted(counts, key=lambda c: (-counts[c], c.category_name))

	@property
	def category(self):
		"""Main category (or None for untagged interests). Kept for older templates."""
		cats = self.categories
		return cats[0] if cats else None


class UserInterest(db.Model):
	__tablename__ = "user_interests"

	user_id = db.Column(
		db.Integer, db.ForeignKey("users.user_id"), primary_key=True
	)
	interest_id = db.Column(
		db.Integer, db.ForeignKey("interests.interest_id"), primary_key=True
	)
	experience_level = db.Column(db.String(30), default="Curious")
	personal_note = db.Column(db.String(255), default="")
	added_at = db.Column(db.DateTime, default=utc_now, nullable=False)

	user = db.relationship("User", back_populates="user_interests")
	interest = db.relationship("Interest", back_populates="user_interests")


class Connection(db.Model):
	__tablename__ = "connections"

	requester_id = db.Column(
		db.Integer, db.ForeignKey("users.user_id"), primary_key=True
	)
	addressee_id = db.Column(
		db.Integer, db.ForeignKey("users.user_id"), primary_key=True
	)
	status = db.Column(db.String(20), default="pending", nullable=False)
	created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
	updated_at = db.Column(
		db.DateTime, default=utc_now, onupdate=utc_now, nullable=False
	)

	requester = db.relationship(
		"User", foreign_keys=[requester_id], back_populates="sent_connections"
	)
	addressee = db.relationship(
		"User", foreign_keys=[addressee_id], back_populates="received_connections"
	)


class ChatRoom(db.Model):
	__tablename__ = "chat_rooms"

	chat_room_id = db.Column(db.Integer, primary_key=True)
	interest_id = db.Column(
		db.Integer,
		db.ForeignKey("interests.interest_id"),
		unique=True,
		nullable=False,
	)
	admin_user_id = db.Column(
		db.Integer, db.ForeignKey("users.user_id"), nullable=True
	)
	room_rules = db.Column(db.Text, default="Be respectful and stay on topic.")
	is_locked = db.Column(db.Boolean, default=False, nullable=False)
	created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

	interest = db.relationship("Interest", back_populates="chat_room")
	admin = db.relationship("User", back_populates="administered_rooms")
	messages = db.relationship(
		"RoomMessage", back_populates="chat_room", cascade="all, delete-orphan"
	)


class RoomMessage(db.Model):
	__tablename__ = "room_messages"

	room_message_id = db.Column(db.Integer, primary_key=True)
	chat_room_id = db.Column(
		db.Integer, db.ForeignKey("chat_rooms.chat_room_id"), nullable=False
	)
	user_id = db.Column(
		db.Integer, db.ForeignKey("users.user_id"), nullable=False
	)
	content = db.Column(db.Text, nullable=False)
	is_pinned = db.Column(db.Boolean, default=False, nullable=False)
	is_deleted = db.Column(db.Boolean, default=False, nullable=False)
	sent_at = db.Column(db.DateTime, default=utc_now, nullable=False)

	chat_room = db.relationship("ChatRoom", back_populates="messages")
	author = db.relationship("User", back_populates="room_messages")


class DirectMessage(db.Model):
	__tablename__ = "direct_messages"

	direct_message_id = db.Column(db.Integer, primary_key=True)
	sender_id = db.Column(
		db.Integer, db.ForeignKey("users.user_id"), nullable=False
	)
	receiver_id = db.Column(
		db.Integer, db.ForeignKey("users.user_id"), nullable=False
	)
	content = db.Column(db.Text, nullable=False)
	is_read = db.Column(db.Boolean, default=False, nullable=False)
	sent_at = db.Column(db.DateTime, default=utc_now, nullable=False)

	sender = db.relationship(
		"User", foreign_keys=[sender_id], back_populates="sent_messages"
	)
	receiver = db.relationship(
		"User", foreign_keys=[receiver_id], back_populates="received_messages"
	)
