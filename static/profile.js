// Profile page behaviour. Everything here is optional: without JavaScript the
// page still works (the dev Preview-as links just reload the page).

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

// ---------- View as (demo): swap the profile body without reloading ----------

const view = document.getElementById("profile-view");
const loadError = document.getElementById("profile-load-error");

async function showAs(link) {
	const url = new URL(link.href);
	url.searchParams.set("partial", "1");

	view.setAttribute("aria-busy", "true");
	loadError.hidden = true;
	try {
		const response = await fetch(url);
		if (!response.ok) throw new Error(response.status);
		view.innerHTML = await response.text();

		// Mark the chosen option, and keep the address bar shareable
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

if (view) {
	document.querySelectorAll(".view-as a").forEach((link) => {
		link.addEventListener("click", (event) => {
			event.preventDefault();
			showAs(link);
		});
	});
}

// ---------- Edit form: counter, contact-detail warning, publish state, live preview ----------

const form = document.getElementById("edit-form");

// Things that look like contact details: an email, a phone number, or an @handle
const CONTACT_PATTERN = /[^\s@]+@[^\s@]+\.[^\s@]+|\+?\d[\d\s().-]{7,}\d|(^|\s)@[A-Za-z0-9._]{2,}/;

function updateEditForm() {
	const bio = form.querySelector("#bio");
	const text = bio.value.trim();
	const publishedText = form.dataset.publishedBio;
	const isPublished = form.dataset.bioPublished === "true" && text === publishedText.trim();

	// Character counter
	form.querySelector("[data-count]").textContent = bio.value.length;

	// Soft warning (never blocks saving)
	form.querySelector("#bio-warning").hidden = !CONTACT_PATTERN.test(text);

	// Publish / Unpublish buttons and status line
	const status = form.querySelector("#bio-status");
	const publish = form.querySelector("#bio-publish");
	const unpublish = form.querySelector("#bio-unpublish");
	publish.hidden = isPublished || !text;
	if (unpublish) unpublish.hidden = !isPublished;

	if (isPublished) {
		status.dataset.state = "published";
		status.textContent = "Published: everyone can see this bio.";
	} else if (!text) {
		status.dataset.state = "draft";
		status.textContent = "No bio: others won't see an About section.";
	} else {
		status.dataset.state = "draft";
		status.textContent = form.dataset.bioPublished === "true"
			? "Edited: saving keeps these changes private until you publish them."
			: "Draft: only you can see this until you publish it.";
	}

	updatePreview(text, isPublished);
}

// Mirror the form into the "How others see you" card
function updatePreview(bioText, isPublished) {
	const name = form.querySelector("#display_name");
	const year = form.querySelector("#year");
	const colour = form.querySelector("input[name=avatar_colour]:checked");

	document.querySelector("[data-preview=name]").textContent = name.value.trim() || name.placeholder;

	const yearLine = document.querySelector("[data-preview=year]");
	yearLine.hidden = year.value === "hide";
	yearLine.textContent = year.value === "hide" ? "" : year.value;

	if (colour) {
		const swatch = colour.closest(".swatch");
		const avatar = document.querySelector("[data-preview=avatar] .avatar");
		avatar.style.setProperty("--avatar", getComputedStyle(swatch).getPropertyValue("--swatch"));
	}

	// Others only see a published bio. Show the draft too, clearly marked.
	const bio = document.querySelector("[data-preview=bio]");
	if (isPublished) {
		bio.dataset.state = "published";
		bio.textContent = bioText;
	} else if (bioText) {
		bio.dataset.state = "draft";
		bio.textContent = bioText;
	} else {
		bio.dataset.state = "hidden";
		bio.textContent = "No bio shown.";
	}
}

if (form) {
	form.addEventListener("input", updateEditForm);
	form.addEventListener("change", updateEditForm);
	updateEditForm();
}
