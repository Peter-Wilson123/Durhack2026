"""
Profile page routes. Every route needs a signed-in user.

	GET /u/                     your own profile
	GET /u/<user_id>            a profile
	GET /u/<user_id>?as=other   owner-only preview as another viewer (debug mode only)
	GET /u/<user_id>/edit       edit page (owner only; saving waits on a backend endpoint)

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
		return None, flask.make_response(
			flask.render_template("profile/error.html",
			                      handle=handle, kind="missing"), 404
		)
	except profile_api.ProfileUnavailable:
		return None, flask.make_response(
			flask.render_template("profile/error.html",
			                      handle=handle, kind="unavailable"), 503
		)
		return None, _error("missing", 404)
	except SQLAlchemyError:
		flask.current_app.logger.exception("Profile lookup failed")
		return None, _error("unavailable", 503)


@bp.get("/u/")
def mine():
	return flask.redirect(flask.url_for("profiles.show", user_id=flask_login.current_user.user_id))


@bp.get("/u/<int:user_id>")
def show(user_id):
	# "View as" is a developer preview, only in debug mode, and only of your own page
	preview_as = flask.request.args.get("as") if flask.current_app.debug else None
	profile, error = _load(user_id, preview_as)
	if error:
		return error
	if flask.request.args.get("partial"):
		return flask.render_template("profile/_body.html", p=profile)
	return flask.render_template(
		"profile/page.html", p=profile, view_as_enabled=flask.current_app.debug and profile["can_preview"]
	)


@bp.get("/u/<int:user_id>/edit")
def edit(user_id):
	profile, error = _load(user_id)
	if error:
		return error
	if profile["viewer_relation"] != "self":
		return _error("forbidden", 403)
	return flask.render_template("profile/edit.html", p=profile)


def init_app(app):
	app.register_blueprint(bp)
