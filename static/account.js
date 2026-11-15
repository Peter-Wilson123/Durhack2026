// Saving profile details through the backend. Shared by profile edit mode
// (profile.js) and Account settings (settings.js).
//
// The backend endpoint is POST /u/<id>/edit (profiles.edit_post, by Peter). It
// sets EVERY field from the form each time (a missing field is saved as empty),
// so we always send all saved values, with only the changed ones replaced.
// It redirects back to the profile when it worked.

// The saved values, from the JSON that templates/account/_fields.html (saved_values) writes
function readSavedProfile() {
	const holder = document.getElementById("profile-saved");
	return holder ? JSON.parse(holder.textContent) : null;
}

// The fields the backend reads from the form
const PROFILE_FIELDS = ["display_name", "year", "avatar_colour", "bio", "instagram", "x", "email"];

// Save `changes` on top of `saved`. action: "save", "publish" or "unpublish" (bio).
// Resolves with the new saved values; throws with a message people can read.
async function saveProfile(saved, changes, action = "save") {
	const values = { ...saved, ...changes };
	const body = new URLSearchParams({ action });
	PROFILE_FIELDS.forEach((field) => body.set(field, values[field] ?? ""));

	let response;
	try {
		response = await fetch(`/u/${saved.user_id}/edit`, { method: "POST", body });
	} catch {
		throw new Error("Couldn't reach the server. Check your connection and try again.");
	}
	const landed = new URL(response.url).pathname;
	if (landed === "/login") throw new Error("You've been signed out. Sign in again, then retry.");
	if (!response.ok || landed !== `/u/${saved.user_id}`) {
		throw new Error("Couldn't save. Please try again.");
	}

	// Mirror what the backend just stored
	const next = { ...values };
	if (values.year !== "hide") next.stored_year = values.year;
	if (!values.bio.trim()) next.bio_published = false;
	else if (action === "publish") next.bio_published = true;
	else if (action === "unpublish") next.bio_published = false;
	else if (values.bio.trim() !== (saved.bio || "").trim()) next.bio_published = false;
	return next;
}

// Friendly checks only: the server is what enforces the rules
function checkProfileValues(values) {
	const errors = {};
	if (values.display_name.trim().length > 30) errors.display_name = "Use 30 characters or fewer.";
	if (values.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(values.email.trim())) {
		errors.email = "That doesn't look like an email address.";
	}
	return errors;
}
