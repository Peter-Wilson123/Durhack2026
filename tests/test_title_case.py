"""
The backend's title case (interest_names.py) against the same cases as the
browser's (static/titleCase.js, tested in tests/test_title_case.js).

Run from the project folder:   python -m unittest tests.test_title_case
"""

import json
import pathlib
import unittest

from interest_names import to_interest_title_case

CASES = json.loads((pathlib.Path(__file__).parent / "title_case_cases.json").read_text())


class TitleCaseTest(unittest.TestCase):
	def test_shared_cases(self):
		for given, expected in CASES:
			with self.subTest(given=given):
				self.assertEqual(to_interest_title_case(given), expected)

	def test_empty(self):
		self.assertEqual(to_interest_title_case(""), "")
		self.assertEqual(to_interest_title_case(None), "")


if __name__ == "__main__":
	unittest.main()
