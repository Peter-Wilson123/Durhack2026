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

**Editing your own profile** happens in place. **Edit profile** turns the same cards into editors, with a Cancel / Done bar.
- **Saved now:** your bio (only through **Publish bio**) and your interests (× to remove, "Add an interest" to add). These use the backend's `POST /update-account`.
- **Not saved yet:** name, year, avatar colour and contacts. They show as disabled inputs until the backend can store them.
- **Suggested for you:** three interests similar to yours.
- **Waves:** still send nothing ("coming soon").

**Preview as others see me** shows your page the way other students see it. The three-way
Me / Connection / Other student switch appears only when Flask runs in debug mode.

**Files**
- `profile_api.py`: data layer, mapping and privacy rules.
- `colours.py`: category colours and short names (keyed by category slug) and the avatar palette.
- `profiles.py`: routes.
- `templates/profile/`: one template per part.
- `static/profile.css` and `static/profile.js`: styles and behaviour.
