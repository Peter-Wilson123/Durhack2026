// Interest names in title case (a pure function: no page, no network).
// Used by home.js in the browser and by tests/test_title_case.js in Node.
// The backend applies the SAME rules before saving (interest_names.py), so
// keep the two in step.

(function (root) {
	// Small words stay lowercase, unless they are the first or last word
	const SMALL_WORDS = new Set(["a", "an", "and", "as", "at", "but", "by", "for", "in", "nor",
		"of", "on", "or", "the", "to", "vs"]);

	// Characters that start a new part of a word, like the hyphen in "rock-climbing"
	const PART_BREAKS = /([-&/])/;

	const isLetter = (ch) => /\p{L}/u.test(ch);

	// A word typed in capitals, with 2 or more letters (CS, DNA, D&D): kept as typed
	function isAllCaps(word) {
		const letters = [...word].filter(isLetter);
		return letters.length >= 2 && letters.every((ch) => ch === ch.toUpperCase() && ch !== ch.toLowerCase());
	}

	// First letter uppercase, every other letter lowercase; symbols kept.
	// A part that starts with a digit is kept as typed ("1970s", "3d", "3D").
	// "don't" -> "Don't", "c++" -> "C++"
	function capitalisePart(part) {
		if (/^\d/.test(part)) return part;
		let done = false;
		return [...part].map((ch) => {
			if (!isLetter(ch)) return ch;
			if (!done) { done = true; return ch.toUpperCase(); }
			return ch.toLowerCase();
		}).join("");
	}

	// Capitalise each part of a word: "rock-climbing" -> "Rock-Climbing", "d&d" -> "D&D"
	function capitaliseWord(word) {
		return word.split(PART_BREAKS).map((part) => (PART_BREAKS.test(part) ? part : capitalisePart(part))).join("");
	}

	// "  lord of   the rings " -> "Lord of the Rings"
	function toInterestTitleCase(name) {
		const words = String(name || "").trim().split(/\s+/).filter(Boolean);
		return words.map((word, i) => {
			if (isAllCaps(word)) return word;
			const isEnd = i === 0 || i === words.length - 1;
			if (!isEnd && SMALL_WORDS.has(word.toLowerCase())) return word.toLowerCase();
			return capitaliseWord(word);
		}).join(" ");
	}

	const api = { toInterestTitleCase };
	if (typeof module !== "undefined" && module.exports) module.exports = api;
	else root.TitleCase = api;
})(this);
