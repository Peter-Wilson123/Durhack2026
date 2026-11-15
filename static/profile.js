// Profile page behaviour (also loaded by the interest page for its Wave buttons).
// Everything here is optional: without JavaScript the profile still shows.

// ---------- Wave ----------
// TODO(backend): there are no wave endpoints yet, so these are STUBS that send
// nothing. Replace each with a POST to the real endpoint once it exists.

// Should create a pending connection from you to this user
function sendWave(userId) {
	return new Promise((resolve) => setTimeout(resolve, 300));
}

// Should mark this user's pending wave to you as accepted
function acceptWave(userId) {
	return new Promise((resolve) => setTimeout(resolve, 300));
}

// Handles clicks on the Wave / Accept wave buttons
document.addEventListener("click", async (event) => {
	const button = event.target.closest("[data-wave]");
	if (!button) return;

	const box = button.closest(".wave");
	const status = box.querySelector(".wave-status");
	const userId = box.dataset.user;

	button.disabled = true;

	try {
		if (button.dataset.wave === "send") {
			await sendWave(userId);
			button.textContent = "Wave (coming soon)";
			status.textContent = "Waving isn't connected to the backend yet, so nothing was sent.";
		} else {
			await acceptWave(userId);
			button.textContent = "Accept wave (coming soon)";
			status.textContent = "Accepting waves isn't connected to the backend yet, so nothing changed.";
		}
		delete button.dataset.wave;
	} catch {
		button.disabled = false;
		status.textContent = "That didn't work. Please try again.";
	}
});

// ---------- Preview as (debug-mode toggle): swap the profile body without reloading ----------

const view = document.getElementById("profile-view");
const loadError = document.getElementById("profile-load-error");

async function showAs(link) {
	const url = new URL(link.href);
	url.searchParams.set("partial", "body");

	view.setAttribute("aria-busy", "true");
	loadError.hidden = true;
	try {
		const response = await fetch(url);
		if (!response.ok) throw new Error(response.status);
		view.innerHTML = await response.text();
		document.querySelectorAll(".view-as a").forEach((a) => a.removeAttribute("aria-current"));
		link.setAttribute("aria-current", "page");
		history.replaceState(null, "", link.href);
	} catch {
		document.getElementById("profile-retry").href = link.href;
		loadError.hidden = false;
	} finally {
		view.removeAttribute("aria-busy");
	}
}

document.querySelectorAll(".view-as a").forEach((link) => {
	link.addEventListener("click", (event) => {
		event.preventDefault();
		showAs(link);
	});
});

// ---------- Saving through the backend ----------
// Profile details and the bio: saveProfile() in account.js (POST /u/<id>/edit).
// Interests: POST /update-account with "new-interests" / "remove-interests".
// It redirects to /account when done.
async function updateAccount(fields) {
	const response = await fetch("/update-account", { method: "POST", body: new URLSearchParams(fields) });
	if (!response.ok || !response.url.endsWith("/account")) throw new Error(response.status);
}

// Fetch one part of this profile again (?partial=interests or suggestions) and swap it in
async function refreshPart(part, extra = {}) {
	const body = document.querySelector(".profile-body");
	const url = new URL(location.pathname, location.origin);
	url.searchParams.set("partial", part);
	Object.entries(extra).forEach(([k, v]) => url.searchParams.set(k, v));
	const response = await fetch(url);
	if (!response.ok) throw new Error(response.status);
	const holder = document.createElement("template");
	holder.innerHTML = await response.text();
	const id = part === "interests" ? "interests-card" : "suggested-card";
	body.querySelector("#" + id)?.replaceWith(holder.content);
}

// ---------- Edit in place (owner only) ----------

const profileBody = () => document.querySelector(".profile-body[data-relation='self']");
const editStatus = () => document.getElementById("edit-status");
const dismissed = new Set();  // suggestions hidden on this page (not saved anywhere)

function say(text) {
	const status = editStatus();
	if (status) status.textContent = text;
}

function setEditing(on) {
	const body = profileBody();
	if (!body) return;
	body.dataset.editing = on ? "true" : "false";
	if (on) {
		say("Editing your profile");
		body.querySelector("#edit-bio")?.focus();
	} else {
		body.querySelector("[data-action='edit']")?.focus();
	}
}

// Bio: has it been changed since it was last saved?
function bioDirty() {
	const editor = document.getElementById("bio-editor");
	const bio = document.getElementById("edit-bio");
	return !!editor && bio.value.trim() !== editor.dataset.savedBio.trim();
}

// Things that look like contact details: an email, a phone number, or an @handle
const CONTACT_PATTERN = /[^\s@]+@[^\s@]+\.[^\s@]+|\+?\d[\d\s().-]{7,}\d|(^|\s)@[A-Za-z0-9._]{2,}/;

function updateBioEditor() {
	const bio = document.getElementById("edit-bio");
	if (!bio) return;
	document.querySelector("#bio-count [data-count]").textContent = bio.value.length;
	document.getElementById("bio-warning").hidden = !CONTACT_PATTERN.test(bio.value);
	const publish = document.querySelector("[data-action='publish-bio']");
	const saved = readSavedProfile();
	// Publishing needs some text, and either new text or a bio that isn't public yet
	publish.disabled = !bio.value.trim() || (!bioDirty() && !!saved?.bio_published);
	document.getElementById("bio-status").textContent = bioDirty() ? "Not published yet" : "";
}

// The name, year, colour and contact inputs shown in edit mode (shared with settings)
const DETAIL_FIELDS = ["display_name", "year", "avatar_colour", "contacts"];

// What the detail inputs hold right now
function detailValues() {
	const body = profileBody();
	const values = {};
	DETAIL_FIELDS.forEach((field) => {
		const inputs = body.querySelectorAll(`#header-fields [name='${field}'], #contact-fields [name='${field}']`);
		if (!inputs.length) return;
		const input = inputs[0].type === "radio" ? [...inputs].find((i) => i.checked) : inputs[0];
		values[field] = input ? input.value.trim() : "";
	});
	return values;
}

// Have any detail inputs changed since the last save?
function detailsDirty() {
	const saved = readSavedProfile();
	if (!saved || !profileBody()) return false;
	return Object.entries(detailValues()).some(([field, value]) => value !== (saved[field] ?? ""));
}

// Put the detail inputs back to the saved values
function resetDetails() {
	const saved = readSavedProfile();
	const body = profileBody();
	if (!saved || !body) return;
	DETAIL_FIELDS.forEach((field) => {
		body.querySelectorAll(`#header-fields [name='${field}'], #contact-fields [name='${field}']`).forEach((input) => {
			if (input.type === "radio") input.checked = input.value === saved[field];
			else input.value = saved[field] ?? "";
			// The contact list redraws itself from its hidden field
			input.dispatchEvent(new Event("contacts-reset"));
		});
	});
	body.querySelectorAll(".field-error").forEach((p) => { p.textContent = ""; });
}

// Remember new saved values in the page
function storeSaved(values) {
	document.getElementById("profile-saved").textContent = JSON.stringify(values);
}

// Publish (or unpublish) the bio through POST /u/<id>/edit
async function setBioPublished(publish) {
	const bio = document.getElementById("edit-bio");
	const status = document.getElementById("bio-status");
	const text = publish ? bio.value.trim() : readSavedProfile().bio;
	status.textContent = publish ? "Publishing…" : "Unpublishing…";
	try {
		const saved = await saveProfile(readSavedProfile(), { bio: text }, publish ? "publish" : "unpublish");
		storeSaved(saved);
		document.getElementById("bio-editor").dataset.savedBio = text;
		// Show the bio in the card when edit mode ends
		const card = document.querySelector(".card-about .view-only");
		const parts = [];
		if (text) parts.push(Object.assign(document.createElement("p"), { className: "bio-text", textContent: text }));
		if (text && !saved.bio_published) {
			parts.push(Object.assign(document.createElement("p"), { className: "card-note", textContent: "Draft · only you can see this" }));
		}
		if (!text) parts.push(Object.assign(document.createElement("p"), { className: "card-empty", textContent: "You haven't written a bio yet." }));
		card.replaceChildren(...parts);
		document.querySelector("[data-action='unpublish-bio']").hidden = !saved.bio_published;
		updateBioEditor();
		status.textContent = saved.bio_published ? "Published" : "Unpublished";
		say(saved.bio_published
			? "Bio published. All verified Durham students can now see it."
			: "Bio unpublished. Only you can see it now.");
	} catch (error) {
		status.textContent = "Not saved. Try again";
		say(error.message);
	}
}

function cancelEdit() {
	const editor = document.getElementById("bio-editor");
	if (editor) {
		document.getElementById("edit-bio").value = editor.dataset.savedBio;
		updateBioEditor();
	}
	resetDetails();
	setEditing(false);
}

// "Done": save changed details, then leave edit mode
async function doneEdit() {
	if (bioDirty() && !confirm("Your bio changes aren't published. Leave edit mode and lose them?")) return;
	if (!detailsDirty()) { cancelEdit(); return; }

	const saved = readSavedProfile();
	const changes = detailValues();
	const errors = checkProfileValues({ ...saved, ...changes });
	document.getElementById("edit-name-error").textContent = errors.display_name || "";
	if (Object.keys(errors).length || !ContactEditor.checkAll(document.getElementById("contact-fields"))) {
		say("Check the highlighted fields.");
		return;
	}

	const done = document.querySelector("[data-action='done-edit']");
	done.disabled = true;
	say("Saving…");
	try {
		// The bio is sent as last saved, so its publish state doesn't change
		await saveProfile(saved, changes, "save");
		window.onbeforeunload = null;
		location.href = `/u/${saved.user_id}`;  // show the saved profile
	} catch (error) {
		done.disabled = false;
		say(error.message);
	}
}

// Remove an interest (× on a pill)
async function removeInterest(button) {
	const name = button.dataset.remove;
	button.disabled = true;
	say(`Removing ${name}…`);
	try {
		await updateAccount({ "remove-interests": name });
		await refreshPart("interests");
		await refreshPart("suggestions", { exclude: [...dismissed].join(",") });
		say(`Removed ${name}.`);
		document.getElementById("add-interest-input")?.focus();
	} catch {
		button.disabled = false;
		say(`Couldn't remove ${name}. Please try again.`);
	}
}

// Add an interest by its exact name (from the search, or a suggestion's "Add")
async function addInterest(name) {
	say(`Adding ${name}…`);
	try {
		await updateAccount({ "new-interests": name });
		await refreshPart("interests");
		await refreshPart("suggestions", { exclude: [...dismissed].join(",") });
		say(`Added ${name}.`);
		const status = document.getElementById("suggest-status");
		if (status) status.textContent = `Added ${name}.`;
		return true;
	} catch {
		say(`Couldn't add ${name}. Please try again.`);
		return false;
	}
}

// Hide a suggestion for now and bring in the next one
async function dismissSuggestion(button) {
	dismissed.add(button.dataset.suggestDismiss);
	button.disabled = true;
	try {
		await refreshPart("suggestions", { exclude: [...dismissed].join(",") });
		document.getElementById("suggest-status").textContent = "Suggestion hidden.";
		document.querySelector("#suggested-card [data-suggest-add]")?.focus();
	} catch {
		button.disabled = false;
	}
}

// ---------- "Add an interest" search box ----------
let addMatches = [];
let addActive = -1;
let addController = null;

async function searchToAdd(input) {
	const list = document.getElementById("add-interest-options");
	const q = input.value.trim();
	addController?.abort();
	if (!q) { hideAddOptions(); return; }
	addController = new AbortController();
	let results = [];
	try {
		const response = await fetch(`/api/interests?q=${encodeURIComponent(q)}`, { signal: addController.signal });
		results = response.ok ? (await response.json()).results : [];
	} catch (e) {
		if (e.name === "AbortError") return;
	}
	if (input.value.trim() !== q) return;

	// Leave out interests already on the profile
	const owned = new Set([...document.querySelectorAll("#interests-card [data-remove]")].map((b) => b.dataset.remove.toLowerCase()));
	addMatches = results.filter((r) => !owned.has(r.name.toLowerCase())).slice(0, 6);
	const options = addMatches.map((r, i) => {
		const li = document.createElement("li");
		li.id = `add-opt-${i}`;
		li.setAttribute("role", "option");
		li.textContent = r.name;
		li.addEventListener("pointerdown", (e) => e.preventDefault());
		li.addEventListener("click", () => chooseToAdd(i));
		return li;
	});
	// Always offer to create it
	const create = document.createElement("li");
	create.id = `add-opt-${addMatches.length}`;
	create.setAttribute("role", "option");
	create.className = "add-create";
	create.textContent = `Create a new interest “${q}”`;
	create.addEventListener("pointerdown", (e) => e.preventDefault());
	create.addEventListener("click", () => chooseToAdd(addMatches.length));
	list.replaceChildren(...options, create);
	list.hidden = false;
	addActive = -1;
	input.setAttribute("aria-expanded", "true");
}

function hideAddOptions() {
	const list = document.getElementById("add-interest-options");
	const input = document.getElementById("add-interest-input");
	if (!list) return;
	list.hidden = true;
	addActive = -1;
	input.setAttribute("aria-expanded", "false");
	input.removeAttribute("aria-activedescendant");
}

function setAddActive(i) {
	const list = document.getElementById("add-interest-options");
	const items = list.children;
	if (!items.length) return;
	addActive = (i + items.length) % items.length;
	[...items].forEach((li, n) => li.setAttribute("aria-selected", String(n === addActive)));
	document.getElementById("add-interest-input").setAttribute("aria-activedescendant", items[addActive].id);
}

async function chooseToAdd(i) {
	const input = document.getElementById("add-interest-input");
	if (i >= addMatches.length) {
		// "Create a new interest": the create form on the home page, pre-filled
		if (bioDirty() && !confirm("Your bio changes aren't published. Leave this page and lose them?")) return;
		window.onbeforeunload = null;
		location.href = `/?q=${encodeURIComponent(input.value.trim())}&create=1`;
		return;
	}
	const name = addMatches[i].name;
	hideAddOptions();
	input.value = "";
	if (await addInterest(name)) document.getElementById("add-interest-input")?.focus();
}

// ---------- Wiring (delegated, because cards are replaced after each change) ----------

document.addEventListener("click", (event) => {
	const target = event.target.closest("[data-action], [data-remove], [data-suggest-add], [data-suggest-dismiss]");
	if (!target || !target.closest(".profile-body[data-relation='self']")) return;

	if (target.dataset.remove) return removeInterest(target);
	if (target.dataset.suggestAdd) { target.disabled = true; return addInterest(target.dataset.suggestAdd); }
	if (target.dataset.suggestDismiss) return dismissSuggestion(target);

	switch (target.dataset.action) {
		case "edit": return setEditing(true);
		case "cancel-edit": return cancelEdit();
		case "done-edit": return doneEdit();
		case "publish-bio": return setBioPublished(true);
		case "unpublish-bio": return setBioPublished(false);
		case "start-adding":
			setEditing(true);
			return document.getElementById("add-interest-input")?.focus();
	}
});

document.addEventListener("input", (event) => {
	if (event.target.id === "edit-bio") updateBioEditor();
	if (event.target.id === "add-interest-input") searchToAdd(event.target);
});

document.addEventListener("keydown", (event) => {
	if (event.target.id === "add-interest-input") {
		const open = !document.getElementById("add-interest-options").hidden;
		if (event.key === "ArrowDown") { event.preventDefault(); if (open) setAddActive(addActive + 1); }
		else if (event.key === "ArrowUp" && open) { event.preventDefault(); setAddActive(addActive - 1); }
		else if (event.key === "Enter" && open) { event.preventDefault(); chooseToAdd(addActive >= 0 ? addActive : 0); }
		else if (event.key === "Escape" && open) { event.preventDefault(); event.stopPropagation(); hideAddOptions(); }
		return;
	}
	// Escape anywhere else in edit mode = Cancel
	if (event.key === "Escape" && profileBody()?.dataset.editing === "true") cancelEdit();
});

document.addEventListener("focusout", (event) => {
	if (event.target.id === "add-interest-input") hideAddOptions();
});

// Warn before leaving the page with an unpublished bio or unsaved details
window.onbeforeunload = (event) => {
	if (bioDirty() || detailsDirty()) { event.preventDefault(); return ""; }
};

// /u/<id>?edit=1 opens straight into edit mode
if (view?.dataset.editOnLoad === "true") setEditing(true);
updateBioEditor();
