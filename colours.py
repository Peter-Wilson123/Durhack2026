"""
Colours used on the profile page. Change them here and nowhere else.

INTEREST_COLOURS: interest category -> pill colours.
  The category names are PROVISIONAL: the team hasn't agreed them yet.
  Add, rename or remove entries freely; anything not listed falls back to
  grey. Every pair is dark text on a pale background, which passes WCAG AA
  contrast (each is well above 4.5 : 1).

AVATAR_COLOURS: the fixed palette people choose their avatar background from.
  The person icon is drawn in white, and white has at least 4.5 : 1 contrast
  on every one of these.
"""

# category: (background, text)
INTEREST_COLOURS = {
	"outdoors": ("#DDF3E4", "#14532D"),  # green
	"tech": ("#DBEAFE", "#1E3A8A"),      # blue
	"creative": ("#FEF3C7", "#78350F"),  # yellow
	"music": ("#FCE7F3", "#831843"),     # pink
	"sport": ("#FFE4D5", "#7C2D12"),     # orange
	"academic": ("#EDE9FE", "#4C1D95"),  # violet
	"social": ("#CCFBF1", "#134E4A"),    # teal
}
INTEREST_FALLBACK = ("#ECEAEE", "#3B3740")  # neutral grey


def interest_colours(category):
	"""(background, text) for a category, or grey if it isn't in the list."""
	return INTEREST_COLOURS.get((category or "").lower(), INTEREST_FALLBACK)


# key: (label shown to people, colour)
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
