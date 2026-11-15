// Interest page behaviour: "Load more" people, and the "+" (add interest) button.
// Wave buttons on the cards are handled by static/profile.js, shared with the profile page.

// ---------- Back button ----------
// Goes back in the browser history when you came here from another page of
// this site. Opened directly (or from another site), it follows its link to "/".
const backButton = document.getElementById("back-button");
if (backButton) {
	backButton.addEventListener("click", (event) => {
		let cameFromThisSite = false;
		try {
			cameFromThisSite = new URL(document.referrer).origin === location.origin;
		} catch { /* no referrer: opened directly */ }
		if (cameFromThisSite && history.length > 1) {
			event.preventDefault();
			history.back();
		}
	});
}

// ---------- "+" button ----------
// Adds or removes this interest from your profile through the backend's
// POST /update-account (it redirects to /account when done), then reloads the
// page so the count, the list and your profile all show the change.
const toggle = document.getElementById("interest-toggle");
if (toggle) {
	toggle.addEventListener("click", async () => {
		const status = document.getElementById("interest-toggle-status");
		const added = toggle.getAttribute("aria-pressed") === "true";
		const field = added ? "remove-interests" : "new-interests";
		toggle.disabled = true;
		status.textContent = added ? "Removing…" : "Adding…";
		try {
			const response = await fetch("/update-account", {
				method: "POST",
				body: new URLSearchParams({ [field]: toggle.dataset.name }),
			});
			if (!response.ok || !response.url.endsWith("/account")) throw new Error(response.status);
			location.reload();
		} catch {
			toggle.disabled = false;
			status.textContent = "That didn't work. Please try again.";
		}
	});
}

// ---------- "Load more" ----------
// Fetches the next page of cards from the server and adds them to the grid.
const moreButton = document.getElementById("people-more");
const grid = document.getElementById("people-grid");
const peopleStatus = document.getElementById("people-status");

async function loadMore(event) {
	event.preventDefault();
	const url = new URL(moreButton.href);
	url.searchParams.set("partial", "people");

	moreButton.textContent = "Loading…";
	moreButton.setAttribute("aria-disabled", "true");
	try {
		const response = await fetch(url);
		if (!response.ok) throw new Error(response.status);

		// Turn the HTML into elements, remember where the new cards start, and add them
		const page = document.createElement("template");
		page.innerHTML = await response.text();
		const info = page.content.querySelector(".people-page-info");
		const firstNew = page.content.querySelector(".user-card");
		grid.querySelectorAll(".people-page-info").forEach((old) => old.remove());
		grid.append(page.content);

		peopleStatus.textContent = `Showing ${info.dataset.shown} people.`;
		if (info.dataset.hasMore === "true") {
			url.searchParams.delete("partial");
			url.searchParams.set("page", info.dataset.next);
			moreButton.href = url;
			moreButton.textContent = "Load more";
			moreButton.removeAttribute("aria-disabled");
		} else {
			moreButton.parentElement.remove();
		}
		// Keyboard users continue from the first new card
		firstNew?.querySelector("a")?.focus();
	} catch {
		moreButton.textContent = "Couldn't load more. Try again";
		moreButton.removeAttribute("aria-disabled");
		peopleStatus.textContent = "Couldn't load more people.";
	}
}

if (moreButton && grid) moreButton.addEventListener("click", loadMore);
