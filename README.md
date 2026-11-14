# Durhack2026

## Profile page: how it works

Open `/u/` for a list of demo profiles, or go straight to `/u/<handle>`.

**Mock data for now.** Every profile comes from `profile_api.py` through
`get_profile(handle)` and is saved through `save_profile(...)`. These use
made-up profiles kept in memory, so edits reset when the server restarts. To
use the real database, rewrite those two functions; the page doesn't need to
change. The profile shape is written out at the top of that file and **hasn't
been agreed with the backend yet**.

**Who sees what** (`viewer_relation`):

| | Other student | Connection | Me |
|---|---|---|---|
| Name, @handle, avatar, interests, connection count | ✓ | ✓ | ✓ |
| Year | only if shown | only if shown | always (badge if hidden) |
| Bio | only if published | only if published | always (badge if draft) |
| Contact details | 🔒 locked + Wave button | ✓ links | ✓ links |
| Edit profile | | | ✓ |

These rules are applied in `get_profile()`, so hidden data is never sent to the
page at all: for other students `contacts` is `None`.

**Bio consent.** A new or changed bio is always a private draft. It only becomes
public when the owner clicks **Publish bio**; **Save changes** never publishes.
The edit page has a live "How others see you" preview, and a gentle warning if
the bio looks like it contains an email, phone number or @handle.

**View as (demo only).** The toggle at the top re-renders the page as Me,
Connection or Other student. Turn it off with `VIEW_AS_ENABLED = False` in
`profiles.py` before using real data.

**Files**

- `profile_api.py`: data layer (mock data, profile shape, privacy rules, saving)
- `colours.py`: interest pill colours by category (names are provisional) and the avatar palette
- `profiles.py`: routes (`/u/`, `/u/<handle>`, `/u/<handle>/edit`)
- `templates/profile/`: one template per part (header, avatar, interests, contact, bio, wave button, view-as toggle, edit form, error page)
- `static/profile.css`, `static/profile.js`: styles, and the toggle, Wave stubs and live edit form

Wave and Accept wave call stub functions (`sendWave`, `acceptWave`) in
`static/profile.js` that should call the backend once it has an endpoint.
`/u/broken_backend` shows the error state.
