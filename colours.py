"""
Category groups, their colours and names, and the avatar palette.
This is the ONE place to change them.

The backend has 20 categories (taxonomy.py). The site shows them as 10
broader GROUPS. CATEGORY_GROUP maps each backend category (by slug, made from
category_name) to a group. If a category is added or renamed in the backend,
add or rename it here too; anything unknown falls back to grey "Other".

Each group has (the site is dark):
  strong  the category hue: dots, borders and tints (--cat); white text on it >= 4.5 : 1
  bg, fg  dark pill background (30% hue over the surface) and light text on it
          (70% white): fg on bg >= 8.3 : 1, fg on the page >= 10.8 : 1

Sport and Recreation are both green, so pages always show the group NAME next
to its colour: never rely on colour alone.
"""

import re

# key: (name, strong, bg, fg) in the order the home page shows them
GROUPS = {
	"science": ("Science", "#0E7490", "#183542", "#B7D5DE"),        # cyan
	"mathematics": ("Mathematics", "#1E3A8A", "#1D2440", "#BCC4DC"),  # dark blue
	"technology": ("Technology", "#6D28D9", "#341E58", "#D3BEF4"),   # purple
	"arts": ("Arts", "#A16207", "#443019", "#E3D0B5"),               # yellow
	"music": ("Music", "#C2410C", "#4E261B", "#EDC6B6"),             # orange
	"humanities": ("Humanities", "#B91C1C", "#4B1B20", "#EABBBB"),   # red
	"society": ("Society", "#4B5563", "#2A2C35", "#C9CCD0"),         # grey
	"practical": ("Practical", "#8A5A2B", "#3D2D24", "#DCCEBF"),     # tan
	"sport": ("Sport", "#166534", "#1A3027", "#B9D1C2"),             # dark green
	"recreation": ("Recreation", "#4D7C0F", "#2B371C", "#CAD8B7"),   # bright green
}
FALLBACK_GROUP = ("Other", "#57534E", "#2E2B2E", "#CDCBCA")

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


def on_dark(hex_colour):
	"""
	A category hue lifted for the dark theme (45% hue, 55% white), used as --cat
	on the home page boxes. Deep hues like dark blue would vanish on the dark
	surface otherwise. Dots are >= 5.6 : 1 on the surface, and ink on its 24%
	tint is >= 9 : 1.
	"""
	h = hex_colour.lstrip("#")
	r, g, b = (round(int(h[i:i + 2], 16) * .45 + 255 * .55) for i in (0, 2, 4))
	return f"#{r:02X}{g:02X}{b:02X}"


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
	"""
	{"categories": {backend slug: group key}, "groups": {group key: {name, colour}}}
	so home.js groups and colours search results from this file. "other" is the
	grey fallback for untagged or unmapped interests.
	"""
	groups = {key: {"name": name, "colour": on_dark(strong)} for key, (name, strong, _bg, _fg) in GROUPS.items()}
	groups["other"] = {"name": FALLBACK_GROUP[0], "colour": on_dark(FALLBACK_GROUP[1])}
	return {"categories": dict(CATEGORY_GROUP), "groups": groups}


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
