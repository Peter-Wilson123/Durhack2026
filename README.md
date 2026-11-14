# Durhack2026

## Profile page: how it works

Sign in, then go to `/u/` for your own profile or `/u/<user id>` for anyone
else's. Signed-out visitors are sent to the sign-in page.

**Real data.** `profile_api.py` reads users, their interests and the
`connections` table, and maps them to the fields the templates use. All
backend names stay in that file. Some fields don't exist in the database yet
(public handle, year, avatar colour, bio drafts, contact details). Those use
fallbacks marked `TODO(backend)`. See
[docs/backend-integration.md](docs/backend-integration.md) for every gap.

**Who sees what** (`viewer_relation`, worked out from the `connections` table):

| | Other student | Connection | Me |
|---|---|---|---|
| Name, avatar, interests (with category), connection count, bio | ✓ | ✓ | ✓ |
| Contact details | 🔒 locked + Wave button | ✓ | ✓ |
| Edit profile | | | ✓ |

The server applies these rules in `get_profile()`, so locked data is never
sent to the page. Profiles use the user ID in URLs because the username is the
CIS code, which must never be shown.

**Not working yet (waiting on backend endpoints):**
- Saving edits. The edit page has a live preview, but its buttons are switched off.
- Sending and accepting waves. The buttons say "coming soon".

**Preview as** (Me / Connection / Other student) appears only on your own
profile and only when Flask runs in debug mode.

**Files**
- `profile_api.py`: data layer, mapping and privacy rules.
- `colours.py`: category colours and short names (keyed by category slug) and the avatar palette.
- `profiles.py`: routes.
- `templates/profile/`: one template per part.
- `static/profile.css` and `static/profile.js`: styles and behaviour.
