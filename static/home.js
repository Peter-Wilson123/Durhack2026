(function () {
	const MAX_RESULTS = 8;

	const home = document.getElementById("home");
	const form = document.getElementById("search-form");
	const input = document.getElementById("search-input");
	const results = document.getElementById("search-results");
	const status = document.getElementById("search-status");
	const closeBtn = document.getElementById("search-close");
	const nameInput = document.getElementById("interest-name");
	const panels = home.querySelectorAll(".panel");

	// Every interest on the page, read from the category grid
	const interests = [...home.querySelectorAll(".interest")].map((a) => ({
		name: a.textContent.trim(),
		href: a.getAttribute("href"),
		cat: a.dataset.category,
		catName: a.dataset.categoryName,
	}));

	let matches = [];
	let active = -1;
	let nameEdited = false;
	let ignoreFocus = false;

	// ---------- States ----------
	function setState(state) {
		if (home.dataset.state === state) return;
		const wasInitial = home.dataset.state === "initial";
		home.dataset.state = state;
		panels.forEach((p) => { p.inert = p.dataset.for !== state; });
		if (wasInitial && window.scrollY > 0) window.scrollTo({ top: 0, behavior: "smooth" });
	}

	function closeSearch() {
		input.value = "";
		nameEdited = false;
		hideResults();
		setState("initial");
		ignoreFocus = true;
		input.focus();
		ignoreFocus = false;
	}

	// ---------- Matching ----------
	function findMatches(q) {
		return interests
			.filter((i) => i.name.toLowerCase().includes(q))
			.sort((a, b) => {
				const as = a.name.toLowerCase().startsWith(q);
				const bs = b.name.toLowerCase().startsWith(q);
				return as === bs ? a.name.localeCompare(b.name) : as ? -1 : 1;
			})
			.slice(0, MAX_RESULTS);
	}

	function update() {
		const raw = input.value.trim();
		const q = raw.toLowerCase();

		if (!q) {
			hideResults();
			status.textContent = "";
			// An empty box never leads to the create form
			if (home.dataset.state !== "initial") setState("search");
			return;
		}

		matches = findMatches(q);

		if (matches.length) {
			setState("search");
			showResults(q);
			status.textContent = `${matches.length} result${matches.length === 1 ? "" : "s"}. Use the arrow keys to choose.`;
		} else {
			hideResults();
			setState("create");
			if (!nameEdited) nameInput.value = raw;
			status.textContent = "No matches. You can create it below.";
		}
	}

	// ---------- Dropdown ----------
	function highlight(name, q) {
		const frag = document.createDocumentFragment();
		const start = name.toLowerCase().indexOf(q);
		frag.append(name.slice(0, start));
		const mark = document.createElement("mark");
		mark.textContent = name.slice(start, start + q.length);
		frag.append(mark, name.slice(start + q.length));
		return frag;
	}

	function showResults(q) {
		active = -1;
		results.replaceChildren(...matches.map((item, i) => {
			const li = document.createElement("li");
			li.id = `result-${i}`;
			li.setAttribute("role", "option");
			li.setAttribute("aria-selected", "false");
			li.style.setProperty("--cat", `var(--cat-${item.cat})`);

			const dot = document.createElement("span");
			dot.className = "result-dot";
			const label = document.createElement("span");
			label.append(highlight(item.name, q));
			const cat = document.createElement("span");
			cat.className = "result-cat";
			cat.textContent = item.catName;

			li.append(dot, label, cat);
			// Keep focus in the input so the dropdown doesn't close before the click lands
			li.addEventListener("pointerdown", (e) => e.preventDefault());
			li.addEventListener("click", () => choose(i));
			return li;
		}));
		results.hidden = false;
		input.setAttribute("aria-expanded", "true");
		input.removeAttribute("aria-activedescendant");
	}

	function hideResults() {
		results.hidden = true;
		active = -1;
		input.setAttribute("aria-expanded", "false");
		input.removeAttribute("aria-activedescendant");
	}

	function setActive(i) {
		const items = results.children;
		if (!items.length) return;
		active = (i + items.length) % items.length;
		[...items].forEach((li, n) => li.setAttribute("aria-selected", String(n === active)));
		items[active].scrollIntoView({ block: "nearest" });
		input.setAttribute("aria-activedescendant", items[active].id);
	}

	function choose(i) {
		const item = matches[i];
		if (item) window.location.href = item.href;
	}

	// ---------- Events ----------
	input.addEventListener("focus", () => {
		if (ignoreFocus) return;
		if (home.dataset.state === "initial") setState("search");
		if (input.value.trim()) update();
	});

	input.addEventListener("click", () => {
		if (home.dataset.state === "initial") setState("search");
	});

	input.addEventListener("blur", hideResults);
	input.addEventListener("input", update);

	input.addEventListener("keydown", (e) => {
		const open = !results.hidden;
		switch (e.key) {
			case "ArrowDown":
				if (open) { e.preventDefault(); setActive(active + 1); }
				else if (input.value.trim()) { e.preventDefault(); update(); }
				break;
			case "ArrowUp":
				if (open) { e.preventDefault(); setActive(active - 1); }
				break;
			case "Enter":
				e.preventDefault();
				if (open) choose(active >= 0 ? active : 0);
				else if (home.dataset.state === "create") document.getElementById("interest-desc").focus();
				break;
			case "Escape":
				e.preventDefault();
				if (open) hideResults();
				else closeSearch();
				break;
		}
	});

	form.addEventListener("submit", (e) => e.preventDefault());
	closeBtn.addEventListener("click", closeSearch);

	// Suggested chips fill in the search
	home.querySelectorAll(".chip").forEach((chip) => {
		chip.addEventListener("click", () => {
			input.value = chip.dataset.interest;
			input.focus();
			update();
		});
	});

	// Quick-link cards
	home.querySelectorAll("[data-go]").forEach((card) => {
		card.addEventListener("click", (e) => {
			e.preventDefault();
			if (card.dataset.go === "search") {
				input.focus();
			} else {
				setState("create");
				nameEdited = false;
				nameInput.value = input.value.trim();
				nameInput.focus({ preventScroll: true });
			}
		});
	});

	nameInput.addEventListener("input", () => { nameEdited = true; });

	// Tag preview chips
	const tagsInput = document.getElementById("interest-tags");
	const tagList = document.getElementById("tag-list");
	tagsInput.addEventListener("input", () => {
		const tags = tagsInput.value.split(/[,\s]+/).map((t) => t.replace(/^#/, "")).filter(Boolean);
		tagList.replaceChildren(...[...new Set(tags)].map((t) => {
			const li = document.createElement("li");
			li.textContent = "#" + t;
			return li;
		}));
	});

	// Start in the initial state (panels other than "initial" become inert)
	panels.forEach((p) => { p.inert = p.dataset.for !== "initial"; });
})();
