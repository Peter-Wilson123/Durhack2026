(function () {
	const GROUP_DEBOUNCE_MS = 250;  // long enough to stop groupings jumping on every key
	const PILLS_PER_GROUP = 8;      // more than this collapse behind "+N more"
	const TAG_DEBOUNCE_MS = 120;
	const PALETTE_SIZE = 8;         // --g0 … --g7 in home.css (only for boxes with no category)
	const MAX_TAGS = 8;
	const TAG_MIN = 2, TAG_MAX = 24;
	const NAME_MIN = 2, NAME_MAX = 40, DESC_MAX = 200;
	const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

	const $ = (id) => document.getElementById(id);
	const home = $("home");
	const input = $("search-input");
	const results = $("search-results");
	const status = $("search-status");
	const groupsEl = $("groups");
	const noteText = $("groups-note-text");
	const createLink = $("groups-create");
	const retryButton = $("groups-retry");
	const nameInput = $("interest-name");  // null when signed out (no create form)
	const categoriesEl = $("categories");
	// Category colours, keyed by backend category slug (from colours.py, the single source)
	const PALETTE = JSON.parse($("category-palette").textContent);
	const slugify = (name) => name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
	const panels = home.querySelectorAll(".panel");

	let nameEdited = false;
	let checkSimilar = () => {};  // replaced by setUpCreateForm() when the form exists
	let ignoreFocus = false;

	// ---------- Small helpers ----------
	function debounce(fn, ms) {
		let t;
		const d = (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
		d.cancel = () => clearTimeout(t);
		return d;
	}

	// Fetch JSON, cancelling the previous request from the same caller
	function latestFetcher() {
		let controller;
		return async (url) => {
			controller?.abort();
			controller = new AbortController();
			try {
				const res = await fetch(url, { signal: controller.signal });
				return res.ok ? res.json() : null;
			} catch (e) {
				if (e.name === "AbortError") return undefined;  // superseded: ignore
				return null;
			}
		};
	}

	function el(tag, props = {}, ...children) {
		const node = document.createElement(tag);
		Object.entries(props).forEach(([k, v]) => {
			if (k === "class") node.className = v;
			else if (k === "style") node.style.cssText = v;
			else if (k in node && !k.includes("-")) node[k] = v;
			else node.setAttribute(k, v);
		});
		node.append(...children);
		return node;
	}

	function highlight(text, q) {
		const i = text.toLowerCase().indexOf(q);
		if (i < 0 || !q) return document.createTextNode(text);
		const frag = document.createDocumentFragment();
		frag.append(text.slice(0, i), el("mark", {}, text.slice(i, i + q.length)), text.slice(i + q.length));
		return frag;
	}

	// ---------- States ----------
	function setState(state) {
		if (home.dataset.state === state) return;
		const wasInitial = home.dataset.state === "initial";
		home.dataset.state = state;
		panels.forEach((p) => { p.inert = !p.dataset.for.split(" ").includes(state); });
		if (wasInitial && window.scrollY > 0) window.scrollTo({ top: 0, behavior: reduceMotion ? "auto" : "smooth" });
	}

	function closeSearch() {
		input.value = "";
		nameEdited = false;
		updateGroups.cancel();
		hideResults();
		showCategories();
		setState("initial");
		ignoreFocus = true;
		input.focus();
		ignoreFocus = false;
	}

	// ---------- Dropdown: interests whose names match (updates every keystroke) ----------
	const fetchMatches = latestFetcher();
	let matches = [];
	let active = -1;

	async function updateDropdown(raw) {
		const q = raw.trim().toLowerCase();
		if (!q) { hideResults(); return; }
		const data = await fetchMatches(`/api/interests?q=${encodeURIComponent(q)}`);
		if (data === undefined || input.value.trim().toLowerCase() !== q) return;
		matches = data?.results || [];
		if (!matches.length || document.activeElement !== input) { hideResults(); return; }

		active = -1;
		results.replaceChildren(...matches.map((item, i) => {
			const li = el("li", { id: `result-${i}`, role: "option", "aria-selected": "false" },
				el("span", { class: "result-dot" }),
				el("span", {}, highlight(item.name, q)),
				el("span", { class: "result-cat" }, item.tags.slice(0, 2).map((t) => "#" + t).join(" ")));
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
		if (matches[i]) window.location.href = matches[i].url;
	}

	// ---------- Groupings: related interests (debounced) ----------
	const fetchDiscover = latestFetcher();
	let groupsShown = false;

	// Empty query: show the 10 category cards (rendered by the server), never tag boxes
	function showCategories() {
		setLoading(false);
		groupsEl.hidden = true;
		categoriesEl.hidden = false;
		setNote("Browse by category", null);
	}

	// Typed query: show tag boxes instead of the category cards
	function showTagBoxes() {
		categoriesEl.hidden = true;
		groupsEl.hidden = false;
	}

	async function runDiscover(raw) {
		const q = raw.trim();
		if (!q) {
			showCategories();
			return;
		}
		setLoading(true);
		const data = await fetchDiscover(`/api/discover?q=${encodeURIComponent(q)}`);
		if (data === undefined) return;  // replaced by a newer search, which is still loading
		setLoading(false);
		if (input.value.trim() !== q) return;
		if (data === null) { showError(() => runDiscover(input.value)); return; }

		if (!data.groups.length) {
			// Nothing related either: offer to create it
			hideResults();
			goToCreate(q);
			status.textContent = "Nothing found. You can create it below.";
			return;
		}

		setState("search");
		const count = data.groups.reduce((n, g) => n + g.interests.length, 0);
		if (data.nameMatches) setNote(`Interests related to “${q}”`, q);
		else setNote(`Nothing called “${q}” yet. These are related:`, q);
		status.textContent = `${count} related interests in ${data.groups.length} groups.`;
		renderGroups(data.groups);
	}
	const updateGroups = debounce(runDiscover, GROUP_DEBOUNCE_MS);

	// Dim the current groups while a search runs, without removing them (the grid keeps its size)
	function setLoading(on) {
		if (on) groupsEl.setAttribute("aria-busy", "true");
		else groupsEl.removeAttribute("aria-busy");
	}

	// Error state: keep whatever is showing and offer a retry
	let retryAction = null;
	function showError(retry) {
		setLoading(false);
		setNote("Couldn't load interests. Check your connection and try again.", null);
		retryAction = retry;
		retryButton.hidden = false;
		status.textContent = "Couldn't load interests.";
	}
	retryButton.addEventListener("click", () => retryAction?.());

	function setNote(text, query) {
		retryButton.hidden = true;
		noteText.textContent = text;
		createLink.hidden = !query;
		if (query) {
			createLink.textContent = `Create “${query}”`;
			createLink.dataset.query = query;
		}
	}

	// Empty state: offer to create what they searched for
	function goToCreate(query) {
		setState("create");
		$("create-title").textContent = query ? `No match for “${query}”. Create it?` : "Create an interest";
		if (nameInput && !nameEdited) {
			nameInput.value = query;
			checkSimilar();
		}
	}

	// Stable colour per grouping while it stays on screen
	const colourOf = new Map();
	function hash(s) { let h = 0; for (const c of s) h = (h * 31 + c.charCodeAt(0)) | 0; return Math.abs(h); }
	function assignColours(keys) {
		for (const k of [...colourOf.keys()]) if (!keys.includes(k)) colourOf.delete(k);
		const used = new Set(colourOf.values());
		for (const k of keys) {
			if (colourOf.has(k)) continue;
			let c = hash(k) % PALETTE_SIZE;
			for (let n = 0; n < PALETTE_SIZE && used.has(c); n++) c = (c + 1) % PALETTE_SIZE;
			colourOf.set(k, c);
			used.add(c);
		}
	}

	// Colours of a box's first category that colours.py knows, or null
	function categoryStyle(g) {
		for (const name of g.categories) {
			const style = PALETTE[slugify(name)];
			if (style) return style;
		}
		return null;
	}

	// The box's category group names (e.g. "Sport"), without repeats
	function groupNames(g) {
		return [...new Set(g.categories.map((name) => PALETTE[slugify(name)]?.name || name))];
	}

	function groupTitle(g) { return g.key.startsWith("__") ? g.title : "#" + g.title; }

	function makeItem(item) {
		return el("li", { "data-flip": "i" + item.id },
			el("a", { class: "group-chip", href: item.url }, item.name));
	}

	function makeGroup(g) {
		const more = el("button", { type: "button", class: "group-more", hidden: true });
		const node = el("section", { class: "group", "data-key": g.key, "data-flip": "g" + g.key },
			el("div", { class: "group-head" },
				el("h3", {}, groupTitle(g)),
				el("p", { class: "group-cats" })),
			el("ul", { class: "group-items" }),
			more);
		// "+N more" reveals the rest of a long group
		more.addEventListener("click", () => {
			node.classList.add("expanded");
			more.hidden = true;
			node.querySelector(`.group-items li:nth-child(${PILLS_PER_GROUP + 1}) a`)?.focus();
		});
		return node;
	}

	function updateMore(node, count) {
		const more = node.querySelector(".group-more");
		const hiddenCount = count - PILLS_PER_GROUP;
		more.hidden = hiddenCount <= 0 || node.classList.contains("expanded");
		more.textContent = `+${hiddenCount} more`;
		more.setAttribute("aria-label", `Show ${hiddenCount} more interests`);
	}

	// Keyed update with FLIP animation: kept elements glide to their new
	// places, new ones fade in, removed ones fade out where they were.
	function renderGroups(groups) {
		const firstReveal = !groupsShown;
		groupsShown = true;
		const before = new Map();
		const box = groupsEl.getBoundingClientRect();
		groupsEl.querySelectorAll("[data-flip]").forEach((n) => before.set(n.dataset.flip, n.getBoundingClientRect()));

		const oldGroups = new Map([...groupsEl.querySelectorAll(":scope > .group")].map((n) => [n.dataset.key, n]));
		const oldItems = new Map([...groupsEl.querySelectorAll("[data-flip^='i']")].map((n) => [n.dataset.flip, n]));

		showTagBoxes();
		assignColours(groups.map((g) => g.key));
		const next = groups.map((g) => {
			const node = oldGroups.get(g.key) || makeGroup(g);
			oldGroups.delete(g.key);
			// Colour the box (and its pills) by its tag's category. TODO(backend): /api/discover
			// doesn't return each interest's own category, so pills share their box's colour.
			const style = categoryStyle(g);
			node.style.setProperty("--g", style ? style.strong : `var(--g${colourOf.get(g.key)})`);
			node.classList.toggle("has-category", !!style);
			if (style) {
				node.style.setProperty("--pill-bg", style.bg);
				node.style.setProperty("--pill-fg", style.fg);
			}
			node.style.setProperty("--n", g.interests.length);
			node.querySelector(".group-cats").textContent = groupNames(g).join(" · ");
			updateMore(node, g.interests.length);
			node.setAttribute("aria-label", `${groupTitle(g)}: ${g.interests.length} interests`);
			const list = node.querySelector(".group-items");
			list.replaceChildren(...g.interests.map((item) => {
				const key = "i" + item.id;
				const existing = oldItems.get(key);
				oldItems.delete(key);
				return existing || makeItem(item);
			}));
			return node;
		});

		groupsEl.replaceChildren(...next);
		if (reduceMotion) return;

		// Leaving groups: fade out at their old position
		oldGroups.forEach((node, key) => {
			const r = before.get("g" + key);
			if (!r) return;
			Object.assign(node.style, {
				position: "absolute", left: `${r.left - box.left}px`, top: `${r.top - box.top}px`,
				width: `${r.width}px`, pointerEvents: "none", margin: 0,
			});
			node.inert = true;
			groupsEl.append(node);
			node.animate([{ opacity: 1 }, { opacity: 0, transform: "scale(.97)" }],
				{ duration: 180, easing: "ease-out" }).onfinish = () => node.remove();
		});

		const glide = (n, dx, dy) => {
			if (Math.abs(dx) < 1 && Math.abs(dy) < 1) return;
			n.animate([{ transform: `translate(${dx}px, ${dy}px)` }, { transform: "none" }],
				{ duration: 380, easing: "cubic-bezier(.2,.7,.2,1)" });
		};

		let entering = 0;
		next.forEach((groupNode, gi) => {
			const gWas = before.get(groupNode.dataset.flip);
			const gNow = groupNode.getBoundingClientRect();
			const gdx = gWas ? gWas.left - gNow.left : 0;
			const gdy = gWas ? gWas.top - gNow.top : 0;
			if (gWas) glide(groupNode, gdx, gdy);

			[groupNode, ...groupNode.querySelectorAll("[data-flip]")].forEach((n) => {
				if (n === groupNode && gWas) return;
				const was = before.get(n.dataset.flip);
				if (was) {
					// Items move with their group already, so only animate the difference
					const now = n.getBoundingClientRect();
					glide(n, was.left - now.left - gdx, was.top - now.top - gdy);
				} else if (n === groupNode || gWas) {
					// New group, or new item in a group that was already there
					const delay = firstReveal ? 120 + gi * 70 : 80 + Math.min(entering++, 8) * 25;
					n.animate([{ opacity: 0, transform: "translateY(6px) scale(.98)" }, { opacity: 1, transform: "none" }],
						{ duration: 320, delay, easing: "cubic-bezier(.2,.7,.2,1)", fill: "backwards" });
				}
			});
		});
	}

	// ---------- Search input events ----------
	function onQuery() {
		const raw = input.value;
		if (!raw.trim()) {
			// Cleared: straight back to the category cards
			hideResults();
			status.textContent = "";
			updateGroups.cancel();
			if (home.dataset.state === "create") setState("search");
			showCategories();
			return;
		}
		updateDropdown(raw);
		updateGroups(raw);
	}

	input.addEventListener("focus", () => {
		if (ignoreFocus) return;
		if (home.dataset.state === "initial") setState("search");
		if (input.value.trim()) updateDropdown(input.value);
	});
	input.addEventListener("click", () => {
		if (home.dataset.state === "initial") setState("search");
	});
	input.addEventListener("blur", hideResults);
	input.addEventListener("input", onQuery);

	input.addEventListener("keydown", (e) => {
		const open = !results.hidden;
		switch (e.key) {
			case "ArrowDown":
				e.preventDefault();
				if (open) setActive(active + 1);
				else updateDropdown(input.value);
				break;
			case "ArrowUp":
				if (open) { e.preventDefault(); setActive(active - 1); }
				break;
			case "Enter":
				e.preventDefault();
				if (open) choose(active >= 0 ? active : 0);
				else if (home.dataset.state === "create") $("interest-desc").focus();
				else if (input.value.trim()) { updateGroups.cancel(); updateGroups(input.value); }
				break;
			case "Escape":
				e.preventDefault();
				if (open) hideResults();
				else closeSearch();
				break;
		}
	});

	$("search-form").addEventListener("submit", (e) => e.preventDefault());
	$("search-close").addEventListener("click", closeSearch);

	createLink.addEventListener("click", () => {
		nameEdited = false;
		goToCreate(createLink.dataset.query || input.value.trim());
		nameInput?.focus({ preventScroll: true });
	});

	// ---------- Create form (only there when signed in) ----------
	if (nameInput) setUpCreateForm();

	function setUpCreateForm() {
		const form = $("create-form");
		const descInput = $("interest-desc");
		const nameError = $("interest-name-error");
		const tagError = $("tag-error");
		const createStatus = $("create-status");
		const submitButton = $("create-submit");

		nameInput.addEventListener("input", () => {
			nameEdited = true;
			nameError.textContent = "";
			checkSimilarSoon();
		});

		// Description counter
		descInput.addEventListener("input", () => {
			form.querySelector("[data-desc-count]").textContent = descInput.value.length;
		});

		// "Did you mean one of these?": up to 3 existing interests with similar names,
		// from the same search the home page uses (GET /api/interests)
		const fetchSimilar = latestFetcher();
		let exactMatch = null;
		checkSimilar = async function () {
			const q = nameInput.value.trim();
			const box = $("similar");
			if (q.length < NAME_MIN) { box.hidden = true; exactMatch = null; return; }
			const data = await fetchSimilar(`/api/interests?q=${encodeURIComponent(q)}`);
			if (data === undefined || nameInput.value.trim() !== q) return;
			const found = (data?.results || []).slice(0, 3);
			exactMatch = found.find((i) => i.name.toLowerCase() === q.toLowerCase()) || null;
			$("similar-list").replaceChildren(...found.map((item) => {
				const add = el("button", { type: "button", class: "btn btn-sm btn-outline-primary" }, "Add this instead");
				add.setAttribute("aria-label", `Add ${item.name} to your interests instead`);
				add.addEventListener("click", () => addExisting(item, add));
				return el("li", {}, el("a", { href: item.url }, item.name), add);
			}));
			box.hidden = !found.length;
		};
		const checkSimilarSoon = debounce(checkSimilar, TAG_DEBOUNCE_MS * 2);

		// Add an existing interest to your profile, then open it
		async function addExisting(item, button) {
			button.disabled = true;
			createStatus.textContent = `Adding ${item.name}…`;
			try {
				await addToMyInterests(item.name);
				window.location.href = item.url;
			} catch {
				button.disabled = false;
				createStatus.textContent = "Couldn't add it. Please try again.";
			}
		}

		// Check the fields; returns true if the form can be sent
		function validate() {
			const name = nameInput.value.trim();
			nameError.textContent = "";
			if (name.length < NAME_MIN || name.length > NAME_MAX) {
				nameError.textContent = `Give it a name of ${NAME_MIN} to ${NAME_MAX} characters.`;
				nameInput.focus();
				return false;
			}
			if (exactMatch) {
				nameError.textContent = `“${exactMatch.name}” already exists. Add it instead, or choose another name.`;
				nameInput.focus();
				return false;
			}
			if (descInput.value.length > DESC_MAX) return false;
			return true;
		}

		// Create through POST /interests/new, add it to your profile, then open it
		form.addEventListener("submit", async (event) => {
			event.preventDefault();
			if (!validate()) return;
			submitButton.disabled = true;
			createStatus.textContent = "Creating…";
			try {
				const response = await fetch(form.action, { method: "POST", body: new FormData(form) });
				// The backend answers with a redirect to the new interest's page
				if (!response.ok || !response.url.includes("/interests/")) throw new Error(response.status);
				await addToMyInterests(nameInput.value.trim());
				createStatus.textContent = "Created. Opening it…";
				window.location.href = response.url;
			} catch {
				submitButton.disabled = false;
				createStatus.textContent = "Couldn't create it. Check your connection and try again.";
			}
		});

		// ---------- Tag chips ----------
		const tagBox = $("tag-input");
		const tagEntry = $("tag-entry");
		const tagChips = $("tag-chips");
		const tagList = $("tag-suggestions");
		const tagValues = $("tag-values");
		const fetchTags = latestFetcher();
		const chosen = [];
		let tagOptions = [];
		let tagActive = -1;

		// Lower case, single spaces, no leading #
		const normalise = (s) => s.trim().toLowerCase().replace(/^#+/, "").replace(/\s+/g, " ");

		function renderChosen() {
			tagChips.replaceChildren(...chosen.map((name) => {
				const remove = el("button", { type: "button", "aria-label": `Remove tag ${name}` }, "×");
				remove.addEventListener("click", () => { removeTag(name); tagEntry.focus(); });
				return el("li", { class: "tag-chip" }, "#" + name, remove);
			}));
			tagValues.replaceChildren(...chosen.map((name) => el("input", { type: "hidden", name: "tags", value: name })));
			const full = chosen.length >= MAX_TAGS;
			tagEntry.disabled = full;
			tagEntry.placeholder = full ? "That’s the maximum" : chosen.length ? "Add another" : "Add a tag";
		}

		function addTag(name) {
			const tag = normalise(name);
			tagError.textContent = "";
			if (!tag) return;
			if (tag.length < TAG_MIN || tag.length > TAG_MAX) {
				tagError.textContent = `Tags need ${TAG_MIN} to ${TAG_MAX} characters.`;
				return;
			}
			if (chosen.includes(tag)) { tagError.textContent = `#${tag} is already added.`; return; }
			if (chosen.length >= MAX_TAGS) { tagError.textContent = `Up to ${MAX_TAGS} tags.`; return; }
			chosen.push(tag);
			tagEntry.value = "";
			renderChosen();
			refreshTagSuggestions();
		}

		function removeTag(name) {
			const i = chosen.indexOf(name);
			if (i >= 0) chosen.splice(i, 1);
			tagError.textContent = "";
			renderChosen();
		}

		async function refreshTagSuggestions() {
			const q = normalise(tagEntry.value);
			const params = new URLSearchParams({ q });
			chosen.forEach((t) => params.append("exclude", t));
			const data = await fetchTags(`/api/tags?${params}`);
			if (data === undefined || normalise(tagEntry.value) !== q || document.activeElement !== tagEntry) return;

			tagOptions = (data?.results || []).map((t) => ({ name: t.name, count: t.count, isNew: false }));
			if (q.length >= TAG_MIN && !tagOptions.some((t) => t.name === q) && !chosen.includes(q)) {
				tagOptions.push({ name: q, isNew: true });
			}
			if (!tagOptions.length) { hideTagSuggestions(); return; }

			tagActive = q ? 0 : -1;
			tagList.replaceChildren(...tagOptions.map((t, i) => {
				const li = t.isNew
					? el("li", { id: `tag-opt-${i}`, role: "option" }, el("span", { class: "new-tag" }, `Create “#${t.name}”`))
					: el("li", { id: `tag-opt-${i}`, role: "option" },
						el("span", {}, "#", highlight(t.name, q)),
						el("span", { class: "count" }, t.count === 1 ? "1 interest" : `${t.count} interests`));
				li.addEventListener("pointerdown", (e) => e.preventDefault());
				li.addEventListener("click", () => { addTag(t.name); tagEntry.focus(); });
				return li;
			}));
			tagList.hidden = false;
			tagEntry.setAttribute("aria-expanded", "true");
			setTagActive(tagActive);
		}
		const refreshTagsSoon = debounce(refreshTagSuggestions, TAG_DEBOUNCE_MS);

		function setTagActive(i) {
			const items = tagList.children;
			if (!items.length) return;
			tagActive = i < 0 ? -1 : (i + items.length) % items.length;
			[...items].forEach((li, n) => li.setAttribute("aria-selected", String(n === tagActive)));
			if (tagActive >= 0) {
				items[tagActive].scrollIntoView({ block: "nearest" });
				tagEntry.setAttribute("aria-activedescendant", items[tagActive].id);
			} else {
				tagEntry.removeAttribute("aria-activedescendant");
			}
		}

		function hideTagSuggestions() {
			tagList.hidden = true;
			tagActive = -1;
			tagEntry.setAttribute("aria-expanded", "false");
			tagEntry.removeAttribute("aria-activedescendant");
		}

		tagBox.addEventListener("click", (e) => { if (e.target === tagBox) tagEntry.focus(); });
		tagEntry.addEventListener("focus", refreshTagSuggestions);
		tagEntry.addEventListener("blur", hideTagSuggestions);
		tagEntry.addEventListener("input", () => {
			// A typed comma adds the tag before it
			if (tagEntry.value.includes(",")) {
				const parts = tagEntry.value.split(",");
				tagEntry.value = parts.pop();
				parts.forEach(addTag);
			}
			refreshTagsSoon();
		});

		tagEntry.addEventListener("keydown", (e) => {
			const open = !tagList.hidden;
			switch (e.key) {
				case "ArrowDown":
					e.preventDefault();
					if (open) setTagActive(tagActive + 1); else refreshTagSuggestions();
					break;
				case "ArrowUp":
					if (open) { e.preventDefault(); setTagActive(tagActive - 1); }
					break;
				case "Enter":
				case ",":
					e.preventDefault();  // never submit the form from here
					if (e.key === "Enter" && open && tagActive >= 0) addTag(tagOptions[tagActive].name);
					else if (tagEntry.value.trim()) addTag(tagEntry.value);
					break;
				case "Backspace":
					if (!tagEntry.value && chosen.length) removeTag(chosen[chosen.length - 1]);
					break;
				case "Escape":
					if (open) { e.preventDefault(); e.stopPropagation(); hideTagSuggestions(); }
					break;
			}
		});

		renderChosen();
	}

	// Add an interest (by its exact name) to the signed-in user's profile.
	// Uses the backend's POST /update-account, which redirects to /account when done.
	async function addToMyInterests(name) {
		const body = new URLSearchParams({ "new-interests": name });
		const response = await fetch("/update-account", { method: "POST", body });
		if (!response.ok || !response.url.endsWith("/account")) throw new Error(response.status);
	}

	// ---------- Start ----------
	panels.forEach((p) => { p.inert = !p.dataset.for.split(" ").includes("initial"); });

	// /?q=… (e.g. from a tag on an interest page) opens straight into a search,
	// and /?q=…&create=1 (from the profile's "Create a new interest") opens the form
	const params = new URLSearchParams(location.search);
	const startQuery = params.get("q");
	if (startQuery && params.get("create")) {
		input.value = startQuery;
		nameEdited = false;
		goToCreate(startQuery);
		nameInput?.focus({ preventScroll: true });
	} else if (startQuery) {
		input.value = startQuery;
		setState("search");
		runDiscover(startQuery);
	}
})();
