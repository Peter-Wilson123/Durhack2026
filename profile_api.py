"""
Profile data layer: reads real users from the database (models.py) and maps
them to the shape the profile templates use. ALL backend field names stay in
this file; templates only ever see the dict below.

Fields the backend can't supply yet use a fallback marked "TODO(backend)".
See docs/backend-integration.md for the full list of gaps.

get_profile(user_id, viewer, preview_as=None) returns:

	id                user_id; used in URLs until the backend adds a public handle
	handle            None: TODO(backend) no public handle exists. users.username
	                  is the CIS code and must NEVER be shown or put in a URL.
	display_name      users.display_name, else "Durham student"
	has_display_name  False when display_name is the fallback
	year, show_year   None, False: TODO(backend) no year column
	avatar_colour     TODO(backend) no column: picked from the palette by user_id
	interests         [{"name", "url", "category", "category_slug"}] from user_interests
	bio               users.bio ("" for none)
	bio_published     True: TODO(backend) no draft column, and bios are already public on /view
	connection_count  accepted rows in connections where the user is either side
	contacts          {} for self and connections: TODO(backend) no contact columns
	                  None for everyone else (the template shows the locked card)
	viewer_relation   "self" | "connection" | "other", worked out from connections
	wave_status       "none" | "sent" | "received", from a pending connections row
	can_preview       True when the viewer is the owner (allows the dev "View as" preview)

Privacy rules are applied HERE, before anything reaches a template.
"""

from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from colours import AVATAR_COLOURS, category_slug, category_style
from models import Connection, Interest, Tag, User, UserInterest, db

RELATIONS = ("self", "connection", "other")
BIO_MAX = 160
NAME_MAX = 30
YEARS = ["Fresher", "2nd year", "3rd year", "4th+", "Postgrad", "Other"]

FALLBACK_NAME = "Durham student"  # TODO(backend): shown when display_name is empty


class ProfileNotFound(Exception):
	pass


# ---------- Reading ----------

def get_profile(user_id, viewer, preview_as=None):
	"""
	The profile of `user_id` as the signed-in `viewer` may see it.
	`preview_as` lets the OWNER preview their page as "connection" or "other";
	it is ignored for anyone else, so it can never reveal more.
	Raises ProfileNotFound.
	"""
	user = db.session.scalar(
		select(User)
		.where(User.user_id == user_id)
		.options(
			selectinload(User.user_interests)
			.selectinload(UserInterest.interest)
			.selectinload(Interest.tags)
			.selectinload(Tag.categories)
		)
	)
	if user is None:
		raise ProfileNotFound(user_id)

	relation, wave_status = _relation(viewer.user_id, user.user_id)
	can_preview = relation == "self"
	if can_preview and preview_as in RELATIONS:
		relation = preview_as

	profile = to_profile(user)
	profile["viewer_relation"] = relation
	profile["wave_status"] = wave_status if relation == "other" else "none"
	profile["can_preview"] = can_preview

	# Privacy: only send what this viewer may see
	if relation != "self":
		if not profile["show_year"]:
			profile["year"] = None
		if not profile["bio_published"]:
			profile["bio"] = ""
	if relation == "other":
		profile["contacts"] = None
	return profile


def to_profile(user):
	"""Map a backend User row to the profile shape (fields everyone may see first)."""
	return {
		"id": user.user_id,
		"handle": None,  # TODO(backend): no public handle; never use user.username (CIS code)
		"display_name": (user.display_name or "").strip() or FALLBACK_NAME,
		"has_display_name": bool((user.display_name or "").strip()),
		"year": None,  # TODO(backend): no year column
		"show_year": False,
		"avatar_colour": fallback_avatar(user.user_id),  # TODO(backend): no avatar colour column
		"interests": [_interest(ui.interest) for ui in user.user_interests],
		"bio": user.bio or "",
		"bio_published": True,  # TODO(backend): no draft/published column
		"connection_count": _connection_count(user.user_id),
		"contacts": {},  # TODO(backend): no contact columns (users.email is the login email, not a contact)
	}


def _interest(interest):
	category = interest.category  # most common category across the interest's tags, or None
	slug = category_slug(category.category_name) if category else None
	return {
		"name": interest.interest_name,
		"url": f"/interests/{interest.interest_id}",
		"category_slug": slug,
		"category": category_style(slug)[0],
	}


def fallback_avatar(user_id):
	keys = list(AVATAR_COLOURS)
	return keys[user_id % len(keys)]


def _connection_count(user_id):
	return db.session.scalar(
		select(func.count())
		.select_from(Connection)
		.where(
			Connection.status == "accepted",
			or_(Connection.requester_id == user_id, Connection.addressee_id == user_id),
		)
	)


def _relation(viewer_id, user_id):
	"""(viewer_relation, wave_status) between the viewer and the profile owner."""
	if viewer_id == user_id:
		return "self", "none"
	row = db.session.scalar(
		select(Connection).where(
			or_(
				(Connection.requester_id == viewer_id) & (Connection.addressee_id == user_id),
				(Connection.requester_id == user_id) & (Connection.addressee_id == viewer_id),
			)
		)
	)
	if row is not None and row.status == "accepted":
		return "connection", "none"
	if row is not None and row.status == "pending":
		# Whoever asked first has "waved"
		return "other", ("sent" if row.requester_id == viewer_id else "received")
	return "other", "none"
