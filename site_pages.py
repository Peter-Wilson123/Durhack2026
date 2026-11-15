"""
Site-wide error pages (404 and 500) inside the shared layout, so they get the
header, dark theme and footer like every other page. Registered from
profiles.init_app so app.py (backend) doesn't need changing.
"""

import flask

bp = flask.Blueprint("site_pages", __name__)


@bp.app_errorhandler(404)
def not_found(_error):
	return flask.render_template("error.html", code=404), 404


@bp.app_errorhandler(500)
def server_error(_error):
	# The layout needs the database (for the signed-in user); if that's what
	# failed, fall back to plain text rather than failing again.
	try:
		return flask.render_template("error.html", code=500), 500
	except Exception:
		return "Something went wrong on our side. Please try again in a moment. (Durham Superposition)", 500


def init_app(app):
	app.register_blueprint(bp)
