"""
Colours and short display names for categories, and the avatar palette.
This is the ONE place to change them.

CATEGORIES is keyed by a slug made from the backend's category_name (see
category_slug). The backend has no slug column, so if a category is renamed
there, rename its key here too. Unknown categories fall back to grey.

Every pair is dark text on a pale background with at least 4.5 : 1 contrast
(WCAG AA). Several categories share a hue family, so the page always shows
the category NAME next to the colour: never rely on colour alone.
"""

import re

# slug: (short name, background, text)
CATEGORIES = {
	"science-and-the-natural-world": ("Science", "#DBEAFE", "#1E3A8A"),
	"mathematics-and-logic": ("Maths", "#E0E7FF", "#312E81"),
	"technology-and-computing": ("Tech", "#CFFAFE", "#164E63"),
	"engineering-and-invention": ("Engineering", "#E2E8F0", "#1E293B"),
	"arts-and-creative-expression": ("Arts", "#FEF3C7", "#78350F"),
	"music-and-performing-arts": ("Music", "#FCE7F3", "#831843"),
	"literature-and-language": ("Literature", "#F3E8FF", "#581C87"),
	"history-and-civilisation": ("History", "#F5E6D3", "#5C3A12"),
	"philosophy-and-intellectual-pursuits": ("Philosophy", "#EDE9FE", "#4C1D95"),
	"religion-and-spirituality": ("Religion", "#FAE8FF", "#701A75"),
	"geography-and-exploration": ("Geography", "#CCFBF1", "#134E4A"),
	"politics-law-and-society": ("Politics", "#FFE4E6", "#881337"),
	"business-and-economics": ("Business", "#E7E5E4", "#292524"),
	"sport-and-physical-activities": ("Sport", "#DCFCE7", "#14532D"),
	"nature-and-outdoor-recreation": ("Outdoors", "#ECFCCB", "#365314"),
	"food-and-culinary-arts": ("Food", "#FFEDD5", "#7C2D12"),
	"games-and-recreation": ("Games", "#FEE2E2", "#7F1D1D"),
	"collecting-and-craftsmanship": ("Crafts", "#FEF9C3", "#713F12"),
	"personal-development-and-lifestyle": ("Lifestyle", "#D1FAE5", "#064E3B"),
	"transport-and-machinery": ("Transport", "#E0F2FE", "#0C4A6E"),
}
CATEGORY_FALLBACK = ("Other", "#ECEAEE", "#3B3740")


def category_slug(category_name):
	"""'Politics, law and society' -> 'politics-law-and-society'"""
	return re.sub(r"[^a-z0-9]+", "-", (category_name or "").lower()).strip("-")


def category_style(slug):
	"""(short name, background, text) for a category slug, or grey 'Other'."""
	return CATEGORIES.get(slug or "", CATEGORY_FALLBACK)


# key: (label shown to people, colour). White icons have at least 4.5 : 1 on each.
AVATAR_COLOURS = {
	"palatinate": ("Palatinate", "#7E317B"),
	"blue": ("Blue", "#1F5FAD"),
	"green": ("Green", "#1E7A4C"),
	"teal": ("Teal", "#0F6E7A"),
	"indigo": ("Indigo", "#4B44A6"),
	"rose": ("Rose", "#A8295E"),
	"rust": ("Rust", "#9A3F12"),
	"slate": ("Slate", "#474552"),
}
AVATAR_DEFAULT = "palatinate"


def avatar_colour(key):
	"""Hex colour for an avatar key, or the default if the key is unknown."""
	return AVATAR_COLOURS.get(key, AVATAR_COLOURS[AVATAR_DEFAULT])[1]
