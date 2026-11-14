"""
Profile page routes.

	GET  /u/                  list of demo profiles
	GET  /u/<handle>          a profile (add ?as=self|connection|other to "view as")
	GET  /u/<handle>?partial=1   just the profile body, for the View-as toggle
	GET  /u/<handle>/edit     edit form (owner only)
	POST /u/<handle>/edit     save edits (owner only)

All data comes from profile_api.py, which is mock data for now.
"""

import flask

import colours
import profile_api

bp = flask.Blueprint("profiles", __name__)

# The "View as" toggle lets anyone see a profile as any relation. That's fine
# for mock data and demos, but must be switched off once data is real.
VIEW_AS_ENABLED = True


def _template_helpers():
	return {
		"interest_colours": colours.interest_colours,
		"avatar_colour": colours.avatar_colour,
		"AVATAR_COLOURS": colours.AVATAR_COLOURS,
		"YEARS": profile_api.YEARS,
		"BIO_MAX": profile_api.BIO_MAX,
		"NAME_MAX": profile_api.NAME_MAX,
		"view_as_enabled": VIEW_AS_ENABLED,
	}


bp.app_context_processor(_template_helpers)


def _load(handle, as_relation=None):
	"""get_profile(), turning failures into the right error page."""
	try:
		return profile_api.get_profile(handle, as_relation), None
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


@bp.get("/u/")
def index():
	return flask.render_template("profile/index.html", profiles=profile_api.demo_handles())


@bp.get("/u/<handle>")
def show(handle):
	as_relation = flask.request.args.get("as") if VIEW_AS_ENABLED else None
	profile, error = _load(handle, as_relation)
	if error:
		return error
	if flask.request.args.get("partial"):
		return flask.render_template("profile/_body.html", p=profile)
	return flask.render_template("profile/page.html", p=profile)


@bp.route("/u/<handle>/edit", methods=["GET", "POST"])
def edit(handle):
	# Only the owner may edit. The mock decides who the owner is; the real
	# backend will compare the handle with the signed-in user instead.
	profile, error = _load(handle)
	if error:
		return error
	if profile["viewer_relation"] != "self":
		return flask.redirect(flask.url_for("profiles.show", handle=handle))

	errors = []
	if flask.request.method == "POST":
		action = flask.request.form.get("action", "save")
		errors = profile_api.save_profile(handle, flask.request.form, action)
		if not errors:
			return flask.redirect(flask.url_for("profiles.edit", handle=handle, saved=action))
		# Show the form again with what they typed
		profile = {**profile, **_form_values(flask.request.form)}

	return flask.render_template(
		"profile/edit.html",
		p=profile,
		errors=errors,
		saved=flask.request.args.get("saved"),
	), (400 if errors else 200)


def _form_values(form):
	year = form.get("year", "")
	return {
		"display_name": form.get("display_name", ""),
		"year": None if year == "hide" else year,
		"show_year": year != "hide",
		"avatar_colour": form.get("avatar_colour", ""),
		"bio": form.get("bio", ""),
		"contacts": {k: form.get(k, "") for k in ("instagram", "x", "email")},
	}


def init_app(app):
	app.register_blueprint(bp)
