"""
Server-side rules for contact methods (the browser's copy, for friendly
messages only, is static/contactTypes.js). Every value is checked here.

validate_contacts(raw) takes the JSON the profile form sends,
	[{"type": "discord", "value": "alex", "label": ""}, …]
and returns (entries, error): a cleaned list, or an error message.
"""

import json
import re

MAX_CONTACTS = 8
CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")

# type: (longest value, pattern the cleaned value must match, message)
RULES = {
	"email": (120, r"[^\s@]+@[^\s@]+\.[^\s@]+", "an email address like name@example.com"),
	"phone": (24, r"\+?[0-9 ()\-.]{7,23}", "a phone number (digits, spaces, + ( ) - .)"),
	"whatsapp": (24, r"\+?[0-9 ()\-.]{7,23}", "a phone number with country code, like +44 7700 900123"),
	"snapchat": (15, r"[A-Za-z][A-Za-z0-9._-]{2,14}", "a Snapchat username (3 to 15 letters, numbers, . _ -)"),
	"discord": (32, r"[a-z0-9._]{2,32}", "a Discord username (2 to 32 lowercase letters, numbers, . _)"),
	"telegram": (32, r"[A-Za-z][A-Za-z0-9_]{4,31}", "a Telegram username (5 to 32 letters, numbers, _)"),
	"instagram": (30, r"[A-Za-z0-9._]{1,30}", "an Instagram username (letters, numbers, . _)"),
	"x": (15, r"[A-Za-z0-9_]{1,15}", "an X username (up to 15 letters, numbers, _)"),
	"linkedin": (100, r"[A-Za-z0-9\-]{3,100}", "your LinkedIn profile name (the part after linkedin.com/in/)"),
	"github": (39, r"[A-Za-z0-9](?:[A-Za-z0-9\-]{0,38})", "a GitHub username"),
	"website": (200, r"https://[^\s<>\"']+\.[^\s<>\"']+", "a web address starting with https://"),
	"other": (100, r".{1,100}", "up to 100 characters"),
}

# Types where a leading @ or a pasted profile link is stripped to the handle
HANDLE_TYPES = {"snapchat", "discord", "telegram", "instagram", "x", "github"}
LINKEDIN_URL = re.compile(r"^(?:https?://)?(?:[a-z]{2,3}\.)?linkedin\.com/in/([^/?#]+)/?.*$", re.I)


def _clean(contact_type, value):
	value = value.strip()
	if contact_type in HANDLE_TYPES:
		value = value.lstrip("@")
	if contact_type == "discord":
		value = value.lower()
	if contact_type == "linkedin":
		match = LINKEDIN_URL.match(value)
		if match:
			value = match.group(1)
	return value


def validate_contacts(raw):
	try:
		items = json.loads(raw or "[]")
	except ValueError:
		return None, "Contact details couldn't be read. Please try again."
	if not isinstance(items, list):
		return None, "Contact details couldn't be read. Please try again."
	if len(items) > MAX_CONTACTS:
		return None, f"You can add up to {MAX_CONTACTS} contact methods."

	entries, seen = [], set()
	for item in items:
		if not isinstance(item, dict):
			return None, "Contact details couldn't be read. Please try again."
		contact_type = str(item.get("type", ""))
		if contact_type not in RULES:
			return None, "Choose a contact type from the list."
		raw_value, raw_label = str(item.get("value", "")), str(item.get("label", "") or "")
		if CONTROL_CHARS.search(raw_value) or CONTROL_CHARS.search(raw_label):
			return None, "Contact details can't contain control characters."
		value = _clean(contact_type, raw_value)
		longest, pattern, wanted = RULES[contact_type]
		if not value:
			return None, "Fill in or remove the empty contact method."
		if len(value) > longest or not re.fullmatch(pattern, value):
			return None, f"{value[:40]} isn't valid: enter {wanted}."

		label = None
		if contact_type == "other":
			label = raw_label.strip()
			if not 2 <= len(label) <= 24:
				return None, "Give your “Other” contact a label of 2 to 24 characters."

		key = (contact_type, value.lower())
		if key in seen:
			return None, "That contact method is already on your list."
		seen.add(key)
		entries.append({"type": contact_type, "value": value, "label": label})
	return entries, None
