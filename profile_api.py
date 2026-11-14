"""
Profile data layer. The profile page gets ALL its data from here.

Right now it serves MOCK data from memory, so the page can be built and demoed
before the backend exists. To switch to real data, rewrite get_profile() and
save_profile() to use the database; nothing else should need to change.

!! The profile shape below is an ASSUMPTION. It has NOT been agreed with the
!! backend team. Every field is listed here so changing it is a one-file edit.

get_profile(handle, as_relation=None) returns a dict:

	handle            str   lowercase a-z 0-9 _, 3-20 chars
	display_name      str   1-30 chars, or None (the page then shows the handle)
	year              str   one of YEARS, or None (hidden or not set)
	show_year         bool  False means the owner chose "Don't show"
	avatar_colour     str   a key of colours.AVATAR_COLOURS, e.g. "palatinate"
	interests         list  [{"name": str, "category": str}]
	bio               str   up to 160 chars ("" if none, or not visible to viewer)
	bio_published     bool  False = private draft only the owner sees
	connection_count  int   number of mutual Wave accepts (never the list)
	contacts          dict  {"instagram": str, "x": str, "email": str}, each may be ""
	                  None  for anyone who isn't the owner or a connection
	viewer_relation   str   "self" | "connection" | "other"
	wave_status       str   "none" | "sent" | "received"  (only means anything for "other")

Privacy rules are applied HERE, not in the template: for a viewer who is not
"self", unpublished bios and hidden years are blanked, and contacts are None
unless the viewer is a connection. The page never receives data it must hide.
"""

import copy
import re

from colours import AVATAR_COLOURS

YEARS = ["Fresher", "2nd year", "3rd year", "4th+", "Postgrad", "Other"]
RELATIONS = ("self", "connection", "other")
BIO_MAX = 160
NAME_MAX = 30


class ProfileNotFound(Exception):
	pass


class ProfileUnavailable(Exception):
	"""The data source failed (e.g. the backend is down)."""


# ---------- Mock data (no real people: names are made up, emails use example.com) ----------

_MOCK = {
	# Opens as the owner's own profile: "Edit profile" button, hidden year, draft bio
	"quiet_heron": {
		"handle": "quiet_heron",
		"display_name": "Quiet Heron",
		"year": "2nd year",
		"show_year": False,
		"avatar_colour": "palatinate",
		"interests": [
			{"name": "Wild swimming", "category": "outdoors"},
			{"name": "Mechanical keyboards", "category": "tech"},
			{"name": "Cyanotype printing", "category": "creative"},
			{"name": "Birdwatching", "category": "outdoors"},
			{"name": "Rust programming", "category": "tech"},
			{"name": "Lino cutting", "category": "creative"},
			{"name": "Pub quizzes", "category": "social"},
		],
		"bio": "Early riser. Usually by the river with binoculars or at a desk soldering something.",
		"bio_published": False,
		"connection_count": 3,
		"contacts": {"instagram": "quiet.heron", "x": "quietheron", "email": "quiet_heron@example.com"},
		"viewer_relation": "self",
		"wave_status": "none",
	},
	# Opens as a connection: real contact links
	"lantern_fox": {
		"handle": "lantern_fox",
		"display_name": "Lantern Fox",
		"year": "3rd year",
		"show_year": True,
		"avatar_colour": "teal",
		"interests": [
			{"name": "Bouldering", "category": "sport"},
			{"name": "Jazz piano", "category": "music"},
			{"name": "Astronomy", "category": "academic"},
			{"name": "Night photography", "category": "creative"},
			{"name": "Board games", "category": "social"},
		],
		"bio": "Climbing three times a week, playing piano badly the rest of it. Ask me about the stars.",
		"bio_published": True,
		"connection_count": 42,
		"contacts": {"instagram": "lantern.fox", "x": "lanternfox", "email": "lantern_fox@example.com"},
		"viewer_relation": "connection",
		"wave_status": "none",
	},
	# Opens as a stranger: contacts locked, "Wave" button
	"moss_badger": {
		"handle": "moss_badger",
		"display_name": "Moss Badger",
		"year": "Fresher",
		"show_year": True,
		"avatar_colour": "green",
		"interests": [
			{"name": "Foraging", "category": "outdoors"},
			{"name": "Folk fiddle", "category": "music"},
			{"name": "Medieval history", "category": "academic"},
			{"name": "Competitive ferret racing", "category": "uncategorised"},
		],
		"bio": "New to Durham. Looking for people to forage with and a folk session to join.",
		"bio_published": True,
		"connection_count": 1,
		"contacts": {"instagram": "", "x": "mossbadger", "email": "moss_badger@example.com"},
		"viewer_relation": "other",
		"wave_status": "none",
	},
	# Opens as a stranger who has waved at you: "Accept wave" button
	"comet_otter": {
		"handle": "comet_otter",
		"display_name": None,  # no display name: the page falls back to the handle
		"year": "Postgrad",
		"show_year": True,
		"avatar_colour": "rose",
		"interests": [
			{"name": "Rowing", "category": "sport"},
			{"name": "Machine learning", "category": "tech"},
			{"name": "Choir", "category": "music"},
		],
		"bio": "Draft bio nobody else should ever see.",
		"bio_published": False,
		"connection_count": 12,
		"contacts": {"instagram": "comet.otter", "x": "", "email": "comet_otter@example.com"},
		"viewer_relation": "other",
		"wave_status": "received",
	},
}

# Handle that pretends the backend is down, to show the error state
_BROKEN_HANDLE = "broken_backend"


def demo_handles():
	"""Mock profiles, for the demo index page."""
	return [(h, p["viewer_relation"], p["wave_status"]) for h, p in _MOCK.items()]


# ---------- Reading ----------

def get_profile(handle, as_relation=None):
	"""
	The profile `handle` as the current viewer may see it.
	`as_relation` overrides viewer_relation (the demo "View as" toggle).
	Raises ProfileNotFound or ProfileUnavailable.
	"""
	handle = (handle or "").lower()
	if handle == _BROKEN_HANDLE:
		raise ProfileUnavailable("Mock backend failure")
	if handle not in _MOCK:
		raise ProfileNotFound(handle)

	profile = copy.deepcopy(_MOCK[handle])
	real_relation = profile["viewer_relation"]
	if as_relation in RELATIONS:
		profile["viewer_relation"] = as_relation
	relation = profile["viewer_relation"]

	# A wave only makes sense between strangers
	if relation != "other" or real_relation != "other":
		profile["wave_status"] = "none"

	# Privacy: strip what this viewer must not receive
	if relation != "self":
		if not profile["show_year"]:
			profile["year"] = None
		if not profile["bio_published"]:
			profile["bio"] = ""
	if relation == "other":
		profile["contacts"] = None

	return profile


# ---------- Writing (owner only) ----------

_SOCIAL_RE = re.compile(r"^[A-Za-z0-9._]{1,30}$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def save_profile(handle, form, action="save"):
	"""
	Validate and store the owner's edits.
	`action` is "save", "publish" or "unpublish" (the bio buttons).
	Returns a list of error messages; an empty list means it saved.
	"""
	stored = _MOCK.get(handle)
	if stored is None:
		raise ProfileNotFound(handle)

	errors = []
	name = " ".join(form.get("display_name", "").split())
	if len(name) > NAME_MAX:
		errors.append(f"Display name must be {NAME_MAX} characters or fewer.")

	year = form.get("year", "")
	if year not in YEARS and year != "hide":
		errors.append("Choose a year from the list.")

	colour = form.get("avatar_colour", "")
	if colour not in AVATAR_COLOURS:
		errors.append("Choose an avatar colour from the palette.")

	bio = form.get("bio", "").strip()
	if len(bio) > BIO_MAX:
		errors.append(f"Bio must be {BIO_MAX} characters or fewer.")

	contacts = {}
	for field, label in (("instagram", "Instagram"), ("x", "X")):
		value = form.get(field, "").strip().lstrip("@")
		if value and not _SOCIAL_RE.match(value):
			errors.append(f"{label} handle can only use letters, numbers, dots and underscores.")
		contacts[field] = value
	email = form.get("email", "").strip()
	if email and not _EMAIL_RE.match(email):
		errors.append("That email address doesn't look right.")
	contacts["email"] = email

	if errors:
		return errors

	stored["display_name"] = name or None
	if year == "hide":
		stored["show_year"] = False
	else:
		stored["year"], stored["show_year"] = year, True
	stored["avatar_colour"] = colour
	stored["contacts"] = contacts

	# A new or changed bio is always a private draft until published
	if bio != stored["bio"]:
		stored["bio_published"] = False
	stored["bio"] = bio
	if action == "publish":
		stored["bio_published"] = bool(bio)
	elif action == "unpublish":
		stored["bio_published"] = False
	return []

