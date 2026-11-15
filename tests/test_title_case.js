// Unit tests for static/titleCase.js
// Run from the project folder:   node --test tests/test_title_case.js
// tests/test_title_case.py checks the backend's copy against the same cases.

const test = require("node:test");
const assert = require("node:assert/strict");
const { toInterestTitleCase } = require("../static/titleCase.js");
const CASES = require("./title_case_cases.json");

test("required examples", () => {
	assert.equal(toInterestTitleCase("rock climbing"), "Rock Climbing");
	assert.equal(toInterestTitleCase("pc building"), "Pc Building");
	assert.equal(toInterestTitleCase("PC building"), "PC Building");
	assert.equal(toInterestTitleCase("lord of the rings"), "Lord of the Rings");
	assert.equal(toInterestTitleCase("board games"), "Board Games");
	assert.equal(toInterestTitleCase("cs"), "Cs");
	assert.equal(toInterestTitleCase("CS"), "CS");
	assert.equal(toInterestTitleCase("  guitar   "), "Guitar");
});

test("every shared case (same list as the backend test)", () => {
	for (const [input, expected] of CASES) {
		assert.equal(toInterestTitleCase(input), expected, JSON.stringify(input));
	}
});

test("empty input gives an empty name", () => {
	assert.equal(toInterestTitleCase(""), "");
	assert.equal(toInterestTitleCase("   "), "");
	assert.equal(toInterestTitleCase(null), "");
});
