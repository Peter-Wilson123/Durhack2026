"""
Interest routes: discovery APIs, creating interests, and interest pages.

Register with `interests.init_app(app)` after the database is set up.
"""

import flask
import flask_login
from sqlalchemy import func, inspect, select

import discovery
import taxonomy
from models import Category, Interest, Tag, db

MAX_TAGS = 10

bp = flask.Blueprint("interests", __name__)


# ---------- JSON APIs used by the home page ----------

@bp.get("/api/interests")
def api_search_interests():
	q = flask.request.args.get("q", "")
	return {"results": [discovery.interest_json(i) for i in discovery.search_interests(q)]}


@bp.get("/api/discover")
def api_discover():
	return discovery.discover(flask.request.args.get("q", ""))


@bp.get("/api/tags")
def api_tags():
	q = flask.request.args.get("q", "")
	exclude = flask.request.args.getlist("exclude")
	return {"results": discovery.suggest_tags(q, exclude=exclude)}


# ---------- Creating and viewing interests ----------

@bp.post("/interests/new")
def create_interest():
	name = " ".join(flask.request.form.get("interest_name", "").split())[:120]
	description = flask.request.form.get("description", "").strip()
	tag_names = flask.request.form.getlist("tags")[:MAX_TAGS]

	if not name:
		return flask.redirect(flask.url_for("home"))

	# Don't create duplicates: send people to the existing interest instead
	existing = db.session.scalar(
		select(Interest).where(func.lower(Interest.interest_name) == name.lower())
	)
	if existing:
		return flask.redirect(flask.url_for("interests.view_interest", interest_id=existing.interest_id))

	user = flask_login.current_user
	interest = Interest(
		interest_name=name,
		description=description,
		created_by_user_id=user.user_id if user.is_authenticated else None,
		tags=discovery.get_or_create_tags(tag_names),  # optional: may be empty
	)
	db.session.add(interest)
	db.session.commit()
	return flask.redirect(flask.url_for("interests.view_interest", interest_id=interest.interest_id))


@bp.get("/interests/<int:interest_id>")
def view_interest(interest_id):
	interest = db.get_or_404(Interest, interest_id)
	return flask.render_template(
		"interest.html",
		interest=interest,
		related=discovery.related_interests(interest),
	)


# ---------- Setup ----------

def seed_taxonomy() -> None:
	"""Load categories, tags and starter interests from taxonomy.py (idempotent)."""
	categories = {c.category_name: c for c in db.session.scalars(select(Category))}
	tags = {t.tag_name: t for t in db.session.scalars(select(Tag))}

	def tag(name):
		if name not in tags:
			tags[name] = Tag(tag_name=name)
			db.session.add(tags[name])
		return tags[name]

	for cat_name, (description, tag_names) in taxonomy.CATEGORIES.items():
		category = categories.get(cat_name)
		if category is None:
			category = categories[cat_name] = Category(category_name=cat_name, description=description)
			db.session.add(category)
		for tag_name in tag_names:
			t = tag(tag_name)
			if category not in t.categories:
				t.categories.append(category)

	existing = set(db.session.scalars(select(func.lower(Interest.interest_name))))
	for name, description, tag_names in taxonomy.INTERESTS:
		if name.lower() not in existing:
			db.session.add(Interest(
				interest_name=name, description=description, tags=[tag(t) for t in tag_names]
			))
	db.session.commit()


def check_schema() -> None:
	"""Stop with a clear message if app.db predates the tags system."""
	columns = {c["name"] for c in inspect(db.engine).get_columns("interests")}
	if "category_id" in columns:
		raise SystemExit(
			"\nYour local database (instance/app.db) is from before interests used tags.\n"
			"Delete instance/app.db and start the app again; it will be rebuilt and seeded.\n"
		)


def init_app(app: flask.Flask) -> None:
	app.register_blueprint(bp)
	with app.app_context():
		db.create_all()
		check_schema()
		if db.session.scalar(select(Tag.tag_id).limit(1)) is None:
			seed_taxonomy()
