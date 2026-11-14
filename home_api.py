"""
Home page data: the 10 category cards shown before anyone types.

TODO(backend): there is no categories endpoint, so this reads interests, their
tags and the tags' categories from the database (models.py) and groups them
with colours.py. Samples are picked at random each time the page is rendered,
so they stay the same until the page is reloaded.
"""

import random

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from colours import GROUPS, category_slug, group_of
from models import Interest, Tag, db

SAMPLES_PER_CARD = 4  # fewer if a group doesn't have that many


def category_cards():
	"""[{key, name, strong, bg, fg, samples: [{name, url}]}] in colours.GROUPS order."""
	interests = db.session.scalars(
		select(Interest).options(selectinload(Interest.tags).selectinload(Tag.categories))
	)
	by_group = {key: [] for key in GROUPS}
	for interest in interests:
		category = interest.category  # most common category across its tags
		key = group_of(category_slug(category.category_name)) if category else None
		if key:
			by_group[key].append(interest)

	cards = []
	for key, (name, strong, bg, fg) in GROUPS.items():
		pool = by_group[key]
		samples = random.sample(pool, min(SAMPLES_PER_CARD, len(pool)))
		cards.append({
			"key": key,
			"name": name,
			"strong": strong,
			"bg": bg,
			"fg": fg,
			"total": len(pool),
			"samples": [{"name": i.interest_name, "url": f"/interests/{i.interest_id}"} for i in samples],
		})
	return cards
