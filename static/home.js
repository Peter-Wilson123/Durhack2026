(function () {
	const filterInput = document.getElementById("interest-search");
	const cards = document.querySelectorAll(".category-card");
	const createTitle = document.getElementById("create-title");
	const createLead = document.getElementById("create-lead");
	const createQuery = document.getElementById("create-query");
	const nameInput = document.getElementById("interest-name");

	// Filter category lists; if nothing matches, switch section 3 to "Not here yet…"
	function filter(query) {
		const q = query.trim().toLowerCase();
		let total = 0;

		cards.forEach((card) => {
			let shown = 0;
			card.querySelectorAll(".interest").forEach((li) => {
				const match = !q || li.dataset.name.includes(q);
				li.hidden = !match;
				if (match) shown++;
			});
			card.querySelector(".no-match").hidden = shown > 0;
			total += shown;
		});

		const notFound = q && total === 0;
		createTitle.textContent = notFound ? "Not here yet…" : "Can’t find yours?";
		createLead.textContent = notFound
			? "Be the first. Add it below and others can join."
			: "Add it, and others who share it can find you.";
		createQuery.hidden = !notFound;
		createQuery.textContent = query.trim();
		if (notFound) nameInput.value = query.trim();

		return total;
	}

	function searchFor(query) {
		filterInput.value = query;
		const total = filter(query);
		const target = query.trim() && total === 0 ? "create" : "search";
		document.getElementById(target).scrollIntoView({ behavior: "smooth" });
	}

	filterInput.addEventListener("input", () => filter(filterInput.value));

	document.getElementById("hero-search").addEventListener("submit", (e) => {
		e.preventDefault();
		searchFor(document.getElementById("hero-search-input").value);
	});

	document.querySelectorAll(".chip").forEach((chip) => {
		chip.addEventListener("click", () => searchFor(chip.dataset.interest));
	});

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
})();
