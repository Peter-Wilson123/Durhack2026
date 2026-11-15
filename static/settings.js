// Account settings (/settings). Each section saves on its own through
// saveProfile() in account.js. The server checks everything; the checks here
// only give friendlier messages.

(function () {
	const detailsForm = document.getElementById("details-form");
	const privacyForm = document.getElementById("privacy-form");
	const showYear = document.getElementById("set-show-year");
	const showYearHelp = document.getElementById("show-year-help");
	const DETAIL_FIELDS = ["display_name", "year", "avatar_colour", "instagram", "x", "email"];

	let saved = readSavedProfile();

	// ---------- Reading the forms ----------

	// What the Profile details inputs hold right now
	function detailValues() {
		const data = new FormData(detailsForm);
		const values = {};
		DETAIL_FIELDS.forEach((field) => { values[field] = (data.get(field) || "").trim(); });
		return values;
	}

	// What the Privacy section asks for, as the backend's "year" field
	function privacyValues() {
		if (showYear.disabled) return {};
		return { year: showYear.checked ? saved.stored_year : "hide" };
	}

	const isDirty = (values) => Object.entries(values).some(([field, value]) => value !== (saved[field] ?? ""));
	const detailsDirty = () => isDirty(detailValues());
	const privacyDirty = () => isDirty(privacyValues());

	// ---------- Keeping both sections in step after a save ----------

	// The year dropdown and the "Show my year" switch store the same thing
	function syncFromSaved() {
		document.getElementById("set-year").value = saved.year;
		showYear.disabled = !saved.stored_year;
		showYear.checked = saved.year !== "hide";
		showYearHelp.textContent = saved.stored_year
			? `Your year (${saved.stored_year}) is shown on your profile when this is on.`
			: "Choose your year in Profile details first.";
	}

	// ---------- Saving a section ----------

	// Run a save, showing "Saving…", then success or the error, in that section
	async function saveSection(form, changes) {
		const status = form.querySelector(".settings-status");
		const button = form.querySelector("button[type='submit']");
		button.disabled = true;
		status.dataset.kind = "";
		status.textContent = "Saving…";
		try {
			saved = await saveProfile(saved, changes);
			syncFromSaved();
			status.dataset.kind = "ok";
			status.textContent = "Saved.";
		} catch (error) {
			status.dataset.kind = "error";
			status.textContent = error.message;
		} finally {
			button.disabled = false;
		}
	}

	detailsForm.addEventListener("submit", (event) => {
		event.preventDefault();
		const values = detailValues();
		const errors = checkProfileValues({ ...saved, ...values });
		document.getElementById("set-name-error").textContent = errors.display_name || "";
		document.getElementById("set-email-error").textContent = errors.email || "";
		if (errors.display_name) { document.getElementById("set-name").focus(); return; }
		if (errors.email) { document.getElementById("set-email").focus(); return; }
		saveSection(detailsForm, values);
	});

	privacyForm.addEventListener("submit", (event) => {
		event.preventDefault();
		saveSection(privacyForm, privacyValues());
	});

	// Clear a section's old "Saved." once it's edited again
	[detailsForm, privacyForm].forEach((form) => {
		form.addEventListener("input", () => {
			const status = form.querySelector(".settings-status");
			if (status.dataset.kind === "ok") { status.textContent = ""; status.dataset.kind = ""; }
		});
	});

	// ---------- Warn before leaving with unsaved changes ----------
	window.addEventListener("beforeunload", (event) => {
		if (detailsDirty() || privacyDirty()) event.preventDefault();
	});
})();
