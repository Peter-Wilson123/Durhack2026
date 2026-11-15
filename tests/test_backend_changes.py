"""
Tests for the small backend fixes listed in BACKEND_CHANGES.md.

Run from the project folder (after `python testdata.py`):
	python -m unittest tests.test_backend_changes

They use the local database (instance/app.db) and remove anything they create.
"""

import unittest

from app import app
from models import Interest, User, db

PASSWORD = "longpassword1"


class BackendChangesTest(unittest.TestCase):
	def setUp(self):
		self.client = app.test_client()

	def tearDown(self):
		# Remove the test users and interests made below
		with app.app_context():
			for name in ("zztest01", "zztest02"):
				user = User.query.filter_by(username=name).first()
				if user:
					db.session.delete(user)
			interest = Interest.query.filter_by(interest_name="Backend Test Interest").first()
			if interest:
				db.session.delete(interest)
			db.session.commit()

	def register(self, username, email):
		return self.client.post("/register", data={
			"username": username, "email": email,
			"password": PASSWORD, "confirm_password": PASSWORD,
		})

	def test_registration_succeeds_instead_of_crashing(self):
		response = self.register("zztest01", "zztest01@durham.ac.uk")
		self.assertEqual(response.status_code, 200)
		with app.app_context():
			self.assertIsNotNone(User.query.filter_by(username="zztest01").first())

	def test_registration_refuses_non_durham_addresses(self):
		response = self.register("zztest02", "zztest02@gmail.com")
		self.assertIn(b"Durham students only", response.data)
		with app.app_context():
			self.assertIsNone(User.query.filter_by(username="zztest02").first())

	def test_update_account_cannot_change_username(self):
		self.client.post("/login", data={"identifier": "alex", "password": "password123"})
		with app.app_context():
			old_bio = db.session.get(User, 1).bio
		self.client.post("/update-account", data={"new-username": "zzhijack", "new-bio": "Test bio"})
		with app.app_context():
			user = db.session.get(User, 1)
			self.assertEqual(user.username, "alex")
			self.assertEqual(user.bio, "Test bio")  # other fields still save
			user.bio = old_bio
			db.session.commit()

	def test_creating_an_interest_needs_sign_in(self):
		self.client.post("/interests/new", data={"interest_name": "Backend Test Interest"})
		with app.app_context():
			self.assertIsNone(Interest.query.filter_by(interest_name="Backend Test Interest").first())

	def test_search_results_include_category_and_score(self):
		data = self.client.get("/api/discover?q=print").get_json()
		items = [i for g in data["groups"] for i in g["interests"]]
		self.assertTrue(items)
		for item in items:
			self.assertIn("category", item)
			self.assertIsInstance(item["score"], (int, float))


if __name__ == "__main__":
	unittest.main()
