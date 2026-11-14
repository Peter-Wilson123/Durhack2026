"""
Category groups, their colours and names, and the avatar palette.
This is the ONE place to change them.

The backend has 20 categories (taxonomy.py). The site shows them as 10
broader GROUPS. CATEGORY_GROUP maps each backend category (by slug, made from
category_name) to a group. If a category is added or renamed in the backend,
add or rename it here too; anything unknown falls back to grey "Other".

Each group has:
  strong  header/border colour, with white text on it   (contrast >= 4.5 : 1)
  bg, fg  pale pill background and dark text on it     (contrast >= 4.5 : 1)

Sport and Recreation are both green, so pages always show the group NAME next
to its colour: never rely on colour alone.
"""

import re

# key: (name, strong, bg, fg) in the order the home page shows them
GROUPS = {
	"science": ("Science", "#0E7490", "#CFFAFE", "#164E63"),        # cyan
	"mathematics": ("Mathematics", "#1E3A8A", "#DBEAFE", "#1E3A8A"),  # dark blue
	"technology": ("Technology", "#6D28D9", "#EDE9FE", "#4C1D95"),   # purple
	"arts": ("Arts", "#A16207", "#FEF9C3", "#713F12"),               # yellow
	"music": ("Music", "#C2410C", "#FFEDD5", "#7C2D12"),             # orange
	"humanities": ("Humanities", "#B91C1C", "#FEE2E2", "#7F1D1D"),   # red
	"society": ("Society", "#4B5563", "#F3F4F6", "#1F2937"),         # grey
	"practical": ("Practical", "#8A5A2B", "#F5E6D3", "#5C3A12"),     # tan
	"sport": ("Sport", "#166534", "#DCFCE7", "#14532D"),             # dark green
	"recreation": ("Recreation", "#4D7C0F", "#ECFCCB", "#365314"),   # bright green
}
FALLBACK_GROUP = ("Other", "#57534E", "#ECEAEE", "#3B3740")

# backend category slug -> group key
CATEGORY_GROUP = {
	"science-and-the-natural-world": "science",
	"mathematics-and-logic": "mathematics",
	"technology-and-computing": "technology",
	"engineering-and-invention": "technology",
	"arts-and-creative-expression": "arts",
	"music-and-performing-arts": "music",
	"literature-and-language": "humanities",
	"history-and-civilisation": "humanities",
	"philosophy-and-intellectual-pursuits": "humanities",
	"religion-and-spirituality": "humanities",
	"politics-law-and-society": "society",
	"business-and-economics": "society",
	"geography-and-exploration": "society",
	"personal-development-and-lifestyle": "society",
	"food-and-culinary-arts": "practical",
	"collecting-and-craftsmanship": "practical",
	"transport-and-machinery": "practical",
	"sport-and-physical-activities": "sport",
	"nature-and-outdoor-recreation": "recreation",
	"games-and-recreation": "recreation",
}


def category_slug(category_name):
	"""'Politics, law and society' -> 'politics-law-and-society'"""
	return re.sub(r"[^a-z0-9]+", "-", (category_name or "").lower()).strip("-")


def group_of(slug):
	"""Group key for a backend category slug, or None if it isn't mapped."""
	return CATEGORY_GROUP.get(slug or "")


def group_style(group_key):
	"""(name, strong, bg, fg) for a group key, or grey 'Other'."""
	return GROUPS.get(group_key or "", FALLBACK_GROUP)


def category_style(slug):
	"""(name, bg, fg) for a backend category slug: the pill colours of its group."""
	name, _strong, bg, fg = group_style(group_of(slug))
	return name, bg, fg


def palette_for_js():
	"""{backend slug: {name, strong, bg, fg}} so home.js colours tag boxes from this file."""
	out = {}
	for slug, key in CATEGORY_GROUP.items():
		name, strong, bg, fg = GROUPS[key]
		out[slug] = {"name": name, "strong": strong, "bg": bg, "fg": fg}
	return out


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
