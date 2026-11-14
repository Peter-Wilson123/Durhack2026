"""
Profile page routes. Every route needs a signed-in user.

	GET /u/                     your own profile
	GET /u/<user_id>            a profile
	GET /u/<user_id>?as=other   owner-only preview as another student sees it
	GET /u/<user_id>?edit=1     your own profile, opened in edit mode
	GET /u/<user_id>/edit       redirects to ?edit=1

Profiles are addressed by user_id for now. TODO(backend): switch to a public
handle once one exists. Never use users.username here: it is the CIS code.
All data comes from profile_api.py.
"""

import flask
import flask_login
from sqlalchemy.exc import SQLAlchemyError

import colours
import profile_api

bp = flask.Blueprint("profiles", __name__)


def _template_helpers():
	return {
		"category_style": colours.category_style,
		"avatar_colour": colours.avatar_colour,
		"AVATAR_COLOURS": colours.AVATAR_COLOURS,
		"YEARS": profile_api.YEARS,
		"BIO_MAX": profile_api.BIO_MAX,
		"NAME_MAX": profile_api.NAME_MAX,
	}


bp.app_context_processor(_template_helpers)


@bp.before_request
def require_sign_in():
	"""Send signed-out visitors to the sign-in page."""
	if not flask_login.current_user.is_authenticated:
		return flask.redirect(flask.url_for("login_get"))


def _error(kind, status):
	return flask.make_response(flask.render_template("profile/error.html", kind=kind), status)


def _load(user_id, preview_as=None):
	"""get_profile(), turning failures into the right error page."""
	try:
		return profile_api.get_profile(user_id, flask_login.current_user, preview_as), None
	except profile_api.ProfileNotFound:
		return None, _error("missing", 404)
	except SQLAlchemyError:
		flask.current_app.logger.exception("Profile lookup failed")
		return None, _error("unavailable", 503)


@bp.get("/u/")
def mine():
	return flask.redirect(flask.url_for("profiles.show", user_id=flask_login.current_user.user_id))


@bp.get("/u/<int:user_id>")
def show(user_id):
	"""
	A profile. The owner sees it editable in place (?edit=1 opens edit mode).
	?as=other or ?as=connection: the owner previews their page as others see it
	(get_profile ignores this for anyone else, so it can never reveal more).
	?partial=body|interests|suggestions returns just that part, for in-page updates.
	"""
	profile, error = _load(user_id, flask.request.args.get("as"))
	if error:
		return error

	partial = flask.request.args.get("partial")
	if partial == "interests":
		return flask.render_template("profile/_interest_tags.html", p=profile)
	if partial == "suggestions":
		if profile["viewer_relation"] != "self":
			return _error("forbidden", 403)
		exclude = [int(x) for x in flask.request.args.get("exclude", "").split(",") if x.isdigit()]
		profile["suggestions"] = profile_api.get_suggestions_for(user_id, exclude)
		return flask.render_template("profile/_suggestions.html", p=profile)
	if partial:
		return flask.render_template("profile/_body.html", p=profile)

	return flask.render_template(
		"profile/page.html",
		p=profile,
		# The three-way "Preview as" switch is a developer tool: debug mode only
		view_as_enabled=flask.current_app.debug and profile["can_preview"],
	)


@bp.get("/u/<int:user_id>/edit")
def edit(user_id):
	"""Old address of the edit page: editing now happens on the profile itself."""
	if user_id != flask_login.current_user.user_id:
		return _error("forbidden", 403)
	return flask.redirect(flask.url_for("profiles.show", user_id=user_id, edit=1))


def init_app(app):
	app.register_blueprint(bp)
