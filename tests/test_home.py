"""
Home page: an empty search shows the 10 category cards; a typed search gives tag boxes.

Run from the project folder:   python -m unittest tests.test_home

It only READS the database (instance/app.db), so run the app or
`python testdata.py` once first so there is data. The switch between the two
views in the browser is done by static/home.js; see the manual test in
docs/backend-integration.md ("Home page: categories before typing").
"""

import re
import unittest

from app import app
from colours import GROUPS


class HomePageTest(unittest.TestCase):
	def setUp(self):
		self.client = app.test_client()

	def test_empty_query_renders_exactly_the_ten_category_cards(self):
		html = self.client.get("/").get_data(as_text=True)
		cards = re.findall(r'class="group category-card" data-category="([a-z]+)"', html)
		self.assertEqual(cards, list(GROUPS))  # all 10, in order
		self.assertEqual(len(cards), 10)
		# Every card shows its name (never colour alone)
		for name, *_ in GROUPS.values():
			self.assertIn(f">{name}</h2>", html)
		# The tag-box container starts empty and hidden: no tags before typing
		self.assertRegex(html, r'<div class="groups" id="groups" hidden></div>')

	def test_category_cards_hold_three_or_four_sample_interests(self):
		html = self.client.get("/").get_data(as_text=True)
		for key in GROUPS:
			card = html.split(f'data-category="{key}"', 1)[1].split("</section>", 1)[0]
			samples = card.count('class="group-chip category-chip"')
			self.assertLessEqual(samples, 4, key)

	def test_typed_query_returns_tag_boxes(self):
		data = self.client.get("/api/discover?q=music").get_json()
		self.assertTrue(data["groups"], "expected at least one tag box for 'music'")
		for box in data["groups"]:
			self.assertTrue(box["title"])        # the box title is a tag (or "Matching names")
			self.assertTrue(box["interests"])    # with the matching interests inside


if __name__ == "__main__":
	unittest.main()
