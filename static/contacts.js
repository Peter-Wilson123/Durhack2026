// Contact methods: showing them on the Contact card, and the editable list used
// by profile edit mode and Account settings (templates/account/_fields.html,
// contact_editor), so the two can't drift apart. Type details come from
// static/contactTypes.js. The server checks everything again when saving.

(function () {
	const { TYPES, MAX_CONTACTS, iconSvg, checkEntry } = window.ContactTypes;

	// Make an element: el("a", { href: "/" }, "text")
	function el(tag, props = {}, ...children) {
		const node = document.createElement(tag);
		Object.entries(props).forEach(([k, v]) => {
			if (k === "class") node.className = v;
			else if (k === "html") node.innerHTML = v;  // only ever our own icon markup
			else node.setAttribute(k, v);
		});
		node.append(...children);
		return node;
	}

	// ---------- Contact card (view) ----------

	// Copy text to the clipboard, falling back to a hidden text box
	async function copyText(text) {
		try {
			await navigator.clipboard.writeText(text);
		} catch {
			const box = el("textarea", { class: "visually-hidden" });
			box.value = text;
			document.body.append(box);
			box.select();
			document.execCommand("copy");
			box.remove();
		}
	}

	// ContactRow: icon, name (or custom label), and the value as a safe link,
	// or with a Copy button for types that have no profile link (Discord, Other)
	function enhanceRow(row) {
		const type = TYPES[row.dataset.type] || TYPES.other;
		const value = row.dataset.value;
		const name = row.dataset.label || type.name;
		row.querySelector(".contact-icon").innerHTML = iconSvg(row.dataset.type);
		row.querySelector(".contact-name").textContent = name;

		const valueEl = row.querySelector(".contact-value");
		const href = type.link ? type.link(value) : null;
		if (href) {
			const isWeb = href.startsWith("https://");
			const link = el("a", { class: "contact-value", href, "aria-label": `${name}: ${value}${isWeb ? " (opens in a new tab)" : ""}` }, value);
			if (isWeb) { link.target = "_blank"; link.rel = "noopener noreferrer"; }
			valueEl.replaceWith(link);
		} else {
			const copy = el("button", { type: "button", class: "contact-copy", "aria-label": `Copy ${name}: ${value}` }, "Copy");
			copy.addEventListener("click", async () => {
				await copyText(value);
				copy.textContent = "Copied";
				setTimeout(() => { copy.textContent = "Copy"; }, 2000);
			});
			row.append(copy);
		}
	}

	document.querySelectorAll(".contact-row").forEach(enhanceRow);

	// ---------- ContactEditor (edit mode and settings) ----------

	// The list as saved: same key order and format as profile_api.contacts_json()
	function serialise(entries) {
		return JSON.stringify(entries.map((e) => ({
			label: TYPES[e.type]?.needsLabel ? (e.label || "").trim() : null,
			type: e.type,
			value: TYPES[e.type] ? TYPES[e.type].clean(e.value || "") : (e.value || ""),
		})));
	}

	function setUpEditor(editor) {
		const hidden = editor.querySelector("input[name='contacts']");
		const list = editor.querySelector(".contact-edit-list");
		const addButton = editor.querySelector("[data-contact-add]");
		const count = editor.querySelector(".contact-count");
		const phoneWarning = editor.querySelector(".contact-phone-warning");
		const prefix = editor.dataset.prefix;
		let rowNumber = 0;

		// Write the list into the hidden field the save code sends
		function sync() {
			const entries = [...list.children].map(readRow);
			hidden.value = serialise(entries);
			const n = entries.length;
			count.textContent = `${n} of ${MAX_CONTACTS} contact methods`;
			addButton.disabled = n >= MAX_CONTACTS;
			phoneWarning.hidden = !entries.some((e) => e.type === "phone" || e.type === "whatsapp");
			hidden.dispatchEvent(new Event("input", { bubbles: true }));  // tells the page it changed
		}

		function readRow(row) {
			return {
				type: row.querySelector("select").value,
				value: row.querySelector(".contact-edit-value").value,
				label: row.querySelector(".contact-edit-label").value,
			};
		}

		// Show (or clear) the message under a row; returns true if it's fine
		function checkRow(row) {
			const message = checkEntry(readRow(row));
			row.querySelector(".field-error").textContent = message;
			row.querySelector(".contact-edit-value").setAttribute("aria-invalid", message ? "true" : "false");
			return !message;
		}

		// ContactEditRow: type, value (and a label for Other), remove
		function makeRow(entry) {
			rowNumber += 1;
			const id = `${prefix}-contact-${rowNumber}`;
			const select = el("select", { class: "form-select form-select-sm", id: id + "-type", "aria-label": "Contact type" },
				...Object.entries(TYPES).map(([key, t]) => el("option", { value: key }, t.name)));
			select.value = entry.type;
			const icon = el("span", { class: "contact-icon", html: iconSvg(entry.type, 18) });
			const value = el("input", { class: "form-control form-control-sm contact-edit-value", id: id + "-value",
				"aria-label": "Contact details", autocomplete: "off", "aria-describedby": id + "-error" });
			value.value = entry.value || "";
			const label = el("input", { class: "form-control form-control-sm contact-edit-label", id: id + "-label",
				"aria-label": "Label for this contact (2 to 24 characters)", placeholder: "Label, e.g. Room", maxlength: "24" });
			label.value = entry.label || "";
			const remove = el("button", { type: "button", class: "contact-remove" }, el("span", { "aria-hidden": "true" }, "×"));
			const error = el("p", { class: "field-error", id: id + "-error", role: "alert" });
			const row = el("li", { class: "contact-edit-row" }, icon, select, label, value, remove, error);

			// Placeholder, length, label field and icon follow the chosen type
			function applyType() {
				const t = TYPES[select.value];
				value.placeholder = t.placeholder;
				value.maxLength = t.max + 10;  // a little room to paste a link or an @
				label.hidden = !t.needsLabel;
				icon.innerHTML = iconSvg(select.value, 18);
				remove.setAttribute("aria-label", `Remove ${t.name} contact`);
			}
			applyType();

			select.addEventListener("change", () => { applyType(); row.querySelector(".field-error").textContent = ""; sync(); });
			value.addEventListener("input", sync);
			label.addEventListener("input", sync);
			value.addEventListener("blur", () => { if (value.value.trim()) checkRow(row); });
			remove.addEventListener("click", () => {
				const next = row.nextElementSibling || row.previousElementSibling;
				row.remove();
				sync();
				(next?.querySelector("select") || addButton).focus();
			});
			return row;
		}

		// Draw the rows from the hidden field's JSON (on load, and after Cancel)
		function render() {
			let entries = [];
			try { entries = JSON.parse(hidden.value || "[]"); } catch { entries = []; }
			list.replaceChildren(...entries.map(makeRow));
			editor.querySelectorAll(".field-error").forEach((p) => { p.textContent = ""; });
			const before = hidden.value;
			sync();
			hidden.value = before;  // drawing must not count as a change
		}

		// "Add contact": a new row with the type list ready to choose from
		addButton.addEventListener("click", () => {
			if (list.children.length >= MAX_CONTACTS) return;
			const row = makeRow({ type: "email", value: "", label: "" });
			list.append(row);
			sync();
			row.querySelector("select").focus();
		});

		hidden.addEventListener("contacts-reset", render);
		editor.checkAll = () => [...list.children].map(checkRow).every(Boolean);
		render();
	}

	document.querySelectorAll("[data-contact-editor]").forEach(setUpEditor);

	// Used before saving: true if every contact row looks fine (messages shown otherwise)
	window.ContactEditor = {
		checkAll(scope) {
			return [...(scope || document).querySelectorAll("[data-contact-editor]")].every((ed) => ed.checkAll());
		},
	};
})();
