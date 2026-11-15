"""
Interest names in title case, applied by the backend before an interest is
saved, so direct API calls get the same result as the create form.

Same rules as static/titleCase.js (the browser copy); tests/title_case_cases.json
holds the cases both are tested against. Keep the two in step.

	"  lord of   the rings " -> "Lord of the Rings"
	"PC building"           -> "PC Building"   (words typed in capitals are kept)
	"rock-climbing"         -> "Rock-Climbing"
"""

import re

# Small words stay lowercase, unless they are the first or last word
SMALL_WORDS = {"a", "an", "and", "as", "at", "but", "by", "for", "in", "nor",
	"of", "on", "or", "the", "to", "vs"}

# Characters that start a new part of a word, like the hyphen in "rock-climbing"
PART_BREAKS = re.compile(r"([-&/])")


def _is_all_caps(word):
	"""A word typed in capitals with 2 or more letters (CS, DNA, D&D): kept as typed."""
	letters = [ch for ch in word if ch.isalpha()]
	return len(letters) >= 2 and all(ch.isupper() for ch in letters)


def _capitalise_part(part):
	"""
	First letter uppercase, other letters lowercase; symbols kept. A part that
	starts with a digit is kept as typed ("1970s", "3d", "3D").
	"""
	if part[:1].isdigit():
		return part
	out, done = [], False
	for ch in part:
		if ch.isalpha():
			out.append(ch.lower() if done else ch.upper())
			done = True
		else:
			out.append(ch)
	return "".join(out)


def _capitalise_word(word):
	return "".join(p if PART_BREAKS.fullmatch(p) else _capitalise_part(p) for p in PART_BREAKS.split(word))


def to_interest_title_case(name):
	words = (name or "").split()
	result = []
	for i, word in enumerate(words):
		if _is_all_caps(word):
			result.append(word)
		elif 0 < i < len(words) - 1 and word.lower() in SMALL_WORDS:
			result.append(word.lower())
		else:
			result.append(_capitalise_word(word))
	return " ".join(result)
