// Contact methods people can share with their connections: ONE place for each
// type's name, icon, placeholder, check and link. To add or rename a type, change
// it here and in contact_types.py (the server, which checks everything; the checks
// here only give friendlier messages).

(function (root) {
	// Small line icons (24×24 paths). Generic shapes, not brand logos.
	const ICONS = {
		mail: '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3.5 6 8.5 7 8.5-7"/>',
		phone: '<path d="M5 4h3l2 5-2.5 1.5a11 11 0 0 0 6 6L15 14l5 2v3a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2Z"/>',
		chat: '<path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12Z"/>',
		camera: '<rect x="3.5" y="3.5" width="17" height="17" rx="5"/><circle cx="12" cy="12" r="4"/>',
		x: '<path d="M5 4l14 16M19 4L5 20"/>',
		briefcase: '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M9 7V5a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v2"/>',
		code: '<path d="m8 8-4 4 4 4M16 8l4 4-4 4"/>',
		globe: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
		dots: '<circle cx="6" cy="12" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="18" cy="12" r="1.5"/>',
	};

	const PHONE = /^\+?[0-9 ()\-.]{7,23}$/;
	const digits = (v) => v.replace(/[^0-9+]/g, "");
	const handle = (v) => v.trim().replace(/^@+/, "");

	// For each type:
	//   name         shown to people        icon     key in ICONS
	//   placeholder  hint in the field      max      longest value
	//   pattern      the value must match   message  what to type instead
	//   clean(v)     tidy what was typed    link(v)  a safe https/mailto/tel link, or null (Copy instead)
	const TYPES = {
		email: {
			name: "Email", icon: "mail", placeholder: "name@example.com", max: 120,
			pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: "Enter an email address like name@example.com.",
			clean: (v) => v.trim(), link: (v) => "mailto:" + encodeURIComponent(v).replace("%40", "@"),
		},
		phone: {
			name: "Phone", icon: "phone", placeholder: "+44 7700 900123", max: 24,
			pattern: PHONE, message: "Enter a phone number using digits, spaces and + ( ) - .",
			clean: (v) => v.trim(), link: (v) => "tel:" + digits(v),
		},
		whatsapp: {
			name: "WhatsApp", icon: "chat", placeholder: "+44 7700 900123", max: 24,
			pattern: PHONE, message: "Enter a phone number with its country code, like +44 7700 900123.",
			clean: (v) => v.trim(), link: (v) => "https://wa.me/" + digits(v).replace("+", ""),
		},
		snapchat: {
			name: "Snapchat", icon: "chat", placeholder: "username", max: 15,
			pattern: /^[A-Za-z][A-Za-z0-9._-]{2,14}$/, message: "Enter a Snapchat username (3 to 15 letters, numbers, . _ -).",
			clean: handle, link: (v) => "https://www.snapchat.com/add/" + encodeURIComponent(v),
		},
		discord: {
			name: "Discord", icon: "chat", placeholder: "username", max: 32,
			pattern: /^[a-z0-9._]{2,32}$/, message: "Enter a Discord username (2 to 32 lowercase letters, numbers, . _).",
			clean: (v) => handle(v).toLowerCase(), link: null,  // no public profile link: Copy instead
		},
		telegram: {
			name: "Telegram", icon: "chat", placeholder: "username", max: 32,
			pattern: /^[A-Za-z][A-Za-z0-9_]{4,31}$/, message: "Enter a Telegram username (5 to 32 letters, numbers, _).",
			clean: handle, link: (v) => "https://t.me/" + encodeURIComponent(v),
		},
		instagram: {
			name: "Instagram", icon: "camera", placeholder: "username", max: 30,
			pattern: /^[A-Za-z0-9._]{1,30}$/, message: "Enter an Instagram username (letters, numbers, . _).",
			clean: handle, link: (v) => "https://www.instagram.com/" + encodeURIComponent(v) + "/",
		},
		x: {
			name: "X", icon: "x", placeholder: "username", max: 15,
			pattern: /^[A-Za-z0-9_]{1,15}$/, message: "Enter an X username (up to 15 letters, numbers, _).",
			clean: handle, link: (v) => "https://x.com/" + encodeURIComponent(v),
		},
		linkedin: {
			name: "LinkedIn", icon: "briefcase", placeholder: "your-name (from linkedin.com/in/your-name)", max: 100,
			pattern: /^[A-Za-z0-9-]{3,100}$/, message: "Enter your LinkedIn profile name, the part after linkedin.com/in/.",
			clean: (v) => {
				const m = v.trim().match(/^(?:https?:\/\/)?(?:[a-z]{2,3}\.)?linkedin\.com\/in\/([^/?#]+)/i);
				return m ? m[1] : v.trim();
			},
			link: (v) => "https://www.linkedin.com/in/" + encodeURIComponent(v) + "/",
		},
		github: {
			name: "GitHub", icon: "code", placeholder: "username", max: 39,
			pattern: /^[A-Za-z0-9][A-Za-z0-9-]{0,38}$/, message: "Enter a GitHub username.",
			clean: handle, link: (v) => "https://github.com/" + encodeURIComponent(v),
		},
		website: {
			name: "Website", icon: "globe", placeholder: "https://example.com", max: 200,
			pattern: /^https:\/\/[^\s<>"']+\.[^\s<>"']+$/, message: "Enter a web address starting with https://.",
			clean: (v) => v.trim(),
			// Only ever an https link, checked again here before use
			link: (v) => { try { return new URL(v).protocol === "https:" ? v : null; } catch { return null; } },
		},
		other: {
			name: "Other", icon: "dots", placeholder: "How to reach you", max: 100, needsLabel: true,
			pattern: /^.{1,100}$/, message: "Use up to 100 characters.",
			clean: (v) => v.trim(), link: null,  // free text is never turned into a link
		},
	};

	const MAX_CONTACTS = 8;
	const CONTROL = /[\x00-\x1f\x7f]/;

	// SVG markup for a type's icon
	function iconSvg(type, size = 20) {
		const key = (TYPES[type] || TYPES.other).icon;
		return `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[key]}</svg>`;
	}

	// Check one entry; returns a message, or "" if it looks fine
	function checkEntry(entry) {
		const type = TYPES[entry.type];
		if (!type) return "Choose a contact type.";
		const value = type.clean(entry.value || "");
		if (!value) return "Fill this in, or remove it.";
		if (CONTROL.test(entry.value || "") || CONTROL.test(entry.label || "")) return "Remove the hidden control characters.";
		if (value.length > type.max || !type.pattern.test(value)) return type.message;
		if (type.needsLabel) {
			const label = (entry.label || "").trim();
			if (label.length < 2 || label.length > 24) return "Give it a label of 2 to 24 characters.";
		}
		return "";
	}

	const api = { TYPES, MAX_CONTACTS, iconSvg, checkEntry };
	if (typeof module !== "undefined" && module.exports) module.exports = api;
	else root.ContactTypes = api;
})(this);
