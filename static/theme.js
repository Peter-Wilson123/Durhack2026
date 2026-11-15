// Light/dark theme switch (the sun/moon button in the menu).
// base.html already applied the saved theme before the page drew; this only
// handles changing it. The choice is stored in this browser only.

(function () {
	const STORAGE_KEY = "superposition-theme";  // same key as the script in base.html
	const PAGE_COLOURS = { dark: "#121016", light: "#FAF8FB" };
	const root = document.documentElement;
	const toggle = document.getElementById("theme-toggle");

	// The theme showing now
	function currentTheme() {
		return root.getAttribute("data-theme") === "light" ? "light" : "dark";
	}

	// Show a theme everywhere: page colours, Bootstrap, native controls, browser bar
	function applyTheme(theme) {
		root.setAttribute("data-theme", theme);
		root.setAttribute("data-bs-theme", theme);
		document.querySelector('meta[name="theme-color"]').content = PAGE_COLOURS[theme];
		document.querySelector('meta[name="color-scheme"]').content = theme;
		updateToggle(theme);
	}

	// Keep the button's label and pressed state in step with the theme
	function updateToggle(theme) {
		if (!toggle) return;
		toggle.setAttribute("aria-pressed", String(theme === "light"));
		toggle.setAttribute("aria-label", theme === "light" ? "Switch to dark mode" : "Switch to light mode");
	}

	// Remember the choice (fails quietly if the browser blocks storage)
	function saveTheme(theme) {
		try { localStorage.setItem(STORAGE_KEY, theme); } catch (e) { /* not saved */ }
	}

	toggle?.addEventListener("click", () => {
		const next = currentTheme() === "light" ? "dark" : "light";
		applyTheme(next);
		saveTheme(next);
	});

	updateToggle(currentTheme());
})();
