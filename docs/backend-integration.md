# Backend integration: what actually exists

Written 14 Nov 2026 from `main` at `c348189`, after reading every Python file and template
on `main` and on the `craig`, `PeterDatabase`, `owen` and `owen2` branches.

## Summary

The integration brief assumed a **FastAPI + Postgres/pgvector** backend and a **React +
Tailwind** frontend. Neither exists. On every branch, the backend is one **Flask** app:

- **App:** Flask 3 with Jinja templates, in `app.py`, plus blueprints.
- **Database:** SQLite at `instance/app.db`, accessed through Flask-SQLAlchemy (`models.py`).
- **Auth:** Flask-Login with a session cookie (see section a.1).
- **Not present:** pgvector, embeddings, semantic search, OpenAPI docs (`/docs`), `.env`,
  `.env.example`, migrations (tables are made by `db.create_all()`), `package.json`.
- **Seed script:** `testdata.py` (5 users, 6 interests, connections, rooms). It drops every
  table when run.
- **Dependencies:** `requirements.txt` lists only `flask` and is UTF-16 encoded.
  Flask-Login and Flask-SQLAlchemy are not listed.

Pages are rendered on the server by Flask. There is no separate frontend, so in this doc
"frontend" means the templates plus the small data layers that feed them (`profile_api.py`,
`discovery.py`).

## ⚠️ Security and privacy problems found (verified by running the app)

1. **Any password signs in.** `auth.load_user()` takes a `password` argument but never
   checks it, and `POST /login` calls it and signs the user in.
   - Signing in as `alex` with the password `WRONG` redirected to `/account` and showed
     Alex's details.
   - Fix: call `user.check_password(password)` in `load_user()`, or in `login_post()`.
2. **Anyone can read any user's email**, even when not signed in. `GET /view/<username>`
   renders `other_user.email`.
   - `/view/maya` showed `maya@uni.ac.uk` to a signed-out visitor.
3. **The CIS code is public.** `User.username` is the CIS code (comment in `login_post`,
   and the sign-in label says "CIS code or username").
   - `/view/<username>` puts it in the URL and prints it on the page.
   - `account.html` prints it too.
4. **No Durham or student check.** `POST /register` accepts any email domain and any
   username, with no verification.
   - Registering `someone@gmail.com` created an account and signed it in.
   - Nothing distinguishes students from staff.
5. **Unknown users don't give a 404.** `/view/<anything>` returns 200 and renders an empty
   profile.

## a) Endpoints

Auth for all of these is the Flask-Login **session cookie** set by `POST /login`. It is
not a bearer token. Unless stated, routes don't require sign-in. "HTML" means a page,
not JSON.

### a.1 Auth (`app.py`, `auth.py`)

| Method | Path | Request | Response | Auth |
|---|---|---|---|---|
| GET | `/login` | – | HTML sign-in form | none |
| POST | `/login` | form: `identifier` (username/CIS code **or** email), `password` | 302 to `/account` on match, else 302 to `/login`. **Password not checked (problem 1).** | none |
| GET | `/logout` | – | 302 to `/login` | none |
| GET/POST | `/register` | form: `username`, `email`, `password`, `confirm_password` | Creates a user and signs them in. Renders `success.html`, or re-renders the form with no message on error. | none |
| – | (unauthorised handler) | – | Routes marked `login_required` render `unauthorized.html` (status 200) | – |

### a.2 Users and profiles

| Method | Path | Request | Response | Auth |
|---|---|---|---|---|
| GET | `/account` | – | HTML: the signed-in user's username, email, interests, categories and bio. Has a form posting to `/update-account`, **which doesn't exist (404)**. | login |
| GET | `/view/<username>` | username or email in the URL | HTML: that user's **username, email**, interests and bio | none (problem 2) |
| GET/POST | `/search` | form: `search` | HTML: users with an interest whose name contains the text (`search.find_users_by_interest`) | none |
| GET | `/find-new-interest` | – | 302 to a recommended `/interests/<id>` | login |
| GET | `/u/`, `/u/<handle>`, `/u/<handle>/edit` | – | Profile page. **Mock data only** (`profile_api.py`), not connected to the database. | none |

There is **no JSON profile endpoint**, **no profile update endpoint**, and **no wave or
connection endpoints** (send, accept or list).

### a.3 Interests, categories, tags and search (`interests.py`, `discovery.py`)

| Method | Path | Request | Response (JSON) | Auth |
|---|---|---|---|---|
| GET | `/api/interests` | `q` | `[{id, name, url, tags[]}]`: up to 8 interests whose name contains `q` | none |
| GET | `/api/discover` | `q` (empty means random) | `{query, nameMatches, groups: [{key, title, categories[], interests: [{id, name, url, tags[]}]}]}` | none |
| GET | `/api/tags` | `q`, `exclude` (repeatable) | `[{name, count, categories[]}]` | none |
| POST | `/interests/new` | form: `interest_name`, `description`, `tags` (repeatable) | 302 to `/interests/<id>` | none |
| GET | `/interests/<id>` | – | HTML interest page with related interests | none |
| GET | `/` | – | HTML home page with search, using `/api/discover` | none |

Search is **tag-based keyword matching**, not semantic. Groups are sorted by relevance,
but `discover()` keeps the scores internally and doesn't return them. There is **no
categories endpoint**: categories reach the page only as names inside `groups[].categories`
and `/api/tags`.

## b) Database tables (`models.py`)

| Table | Columns | Relations |
|---|---|---|
| `users` | `user_id` PK, `username` unique (**CIS code**), `display_name` nullable, `email` unique, `password_hash`, `bio` text, `avatar_url`, `created_at` | `user_interests`, `sent_connections`, `received_connections`, `created_interests`, rooms, messages |
| `categories` | `category_id` PK, `category_name` unique, `description` | many-to-many with `tags` through `tag_categories` |
| `tags` | `tag_id` PK, `tag_name` unique (lower case), `created_at` | many-to-many with `categories` and with `interests` (`interest_tags`) |
| `interests` | `interest_id` PK, `interest_name` unique, `description`, `cover_image_url`, `created_by_user_id` FK nullable, `created_at` | `tags`; `categories` and `category` are derived from the tags (Python properties, not columns) |
| `user_interests` | `user_id` + `interest_id` PK, `experience_level`, `personal_note`, `added_at` | joins users and interests |
| `connections` | `requester_id` + `addressee_id` PK, `status` (`"pending"`/`"accepted"`, default `"pending"`), `created_at`, `updated_at` | two FKs to `users` |
| `chat_rooms`, `room_messages`, `direct_messages` | (not relevant here) | |

The chain is Category → Tags → Interests. An interest has **no category column**: it gets
its categories through its tags, and `Interest.category` is the most common one. There are
**20 categories** (seeded from `taxonomy.py`), not 10.

## c) Field mapping

| Frontend needs | Comes from | Status |
|---|---|---|
| `handle` | Nothing public. `users.username` is the CIS code, so it **must not** be used. | **MISSING** |
| `display_name` | `users.display_name` (nullable) | ✓ (read only: no update endpoint) |
| `year` | – | **MISSING** |
| `avatar_colour` | – (`users.avatar_url` exists but holds an image URL, not a palette key) | **MISSING** |
| `bio` | `users.bio` | ✓ (read only) |
| `bio_published` | – | **MISSING**: today every bio is public |
| `connection_count` | `connections` rows with `status = "accepted"` where the user is `requester_id` or `addressee_id` | Derivable, no endpoint |
| `contacts` | – (only `users.email`, which `/view` leaks) | **MISSING** |
| `viewer_relation` | Derivable: signed-in `user_id` equal to the profile's means `self`; an accepted `connections` row means `connection`; otherwise `other` | Derivable, no endpoint |
| wave state (sent/received) | Derivable from `connections` with `status = "pending"` and its direction | Derivable; **no endpoints to send or accept** |
| interests with category | `user_interests` → `interests` → `tags` → `categories` (`Interest.category`) | Derivable (an interest may have no category) |
| categories (10) with sample interests | `categories` → `tags` → `interests` (20 categories) | Derivable, **no endpoint**; the count is 20 |
| tag-grouped results `[{tag, score, interests[]}]` | `GET /api/discover`: `groups[].title` is the tag, `groups[].interests`. Groups come back already sorted. | ✓ but **no `score`** and **not semantic** |
| category slug (for colours) | – (`category_name` only, e.g. "Science and Technology") | **MISSING** (slug derivable from the name) |

## Gaps for Craig and Peter

**Security (fix first)**
1. Check the password at sign-in (problem 1).
2. Stop `/view/<username>` showing the email to anyone, and return 404 for unknown users
   (problems 2 and 5).
3. Stop using the CIS code as a public identifier: add a separate public `handle` column
   (lowercase a-z, 0-9 and `_`, 3–20 characters) and use it in URLs (problem 3).

**Durham-only sign-in**
4. Accept only student `@durham.ac.uk` addresses, verify them by email link or code, and
   decide how staff are told apart from students (problem 4). The backend should be the
   only source for the allowed email format.

**New profile fields**
5. Add `year`, `show_year`, `avatar_colour`, `bio_published` and contact fields
   (`contact_instagram`, `contact_x`, `contact_email`). Default `bio_published` to false.

**New endpoints**
6. A profile read endpoint (JSON, or keep it server-rendered) that applies the privacy
   rules **on the server**:
   - contacts only for self and connections;
   - unpublished bios and hidden years only for self.
7. A profile update endpoint, with publish and unpublish for the bio.
   `account.html` already posts to `/update-account`, which doesn't exist.
8. Wave endpoints:
   - send a wave (creates a pending `connections` row);
   - accept a wave (sets the status to `accepted`);
   - optionally list waves received.

**Data and search**
9. A categories endpoint (slug, name, sample interests), if the home page should show a
   category grid.
10. Semantic search (pgvector) if it's still planned. Today search is keyword plus tag
    relations, and it doesn't return scores.

**Setup and running**
11. `requirements.txt`: save it as UTF-8 and add `flask-login` and `flask-sqlalchemy`.
12. Login is required on almost nothing. `/`, `/search`, `/view`, `/api/*`, `/interests/*`
    and `/u/*` are all public.
13. CORS: not needed while everything is served by Flask on one origin.
14. The secret key is hard-coded in `app.py` (`change-this-hackathon-secret`).

## Privacy check (current state)

- **Contacts withheld server-side?** There are no contact fields. The only contact detail
  is `users.email`, and it is **not** withheld: `/view/<username>` shows it to anyone.
- **CIS code withheld?** **No.** It is in `/view/<username>` URLs, printed on `/view` and
  `/account`, and asked for on the sign-in form.
- The mock profile page (`/u/…`) withholds contacts, drafts and hidden years on the
  server, but it uses made-up data and no real user records.

## What the frontend does with each gap (temporary fallbacks)

All of these are marked `TODO(backend)` in the code.

| Missing | Fallback | Where |
|---|---|---|
| public `handle` | Profiles live at `/u/<user_id>`. No @handle is shown. | `profiles.py`, `profile_api.py` |
| `display_name` empty | "Durham student" (never the username) | `profile_api.FALLBACK_NAME` |
| `year` | Not shown | `profile_api.to_profile` |
| `avatar_colour` | Picked from the palette by `user_id` | `profile_api._fallback_avatar` |
| `bio_published` | Treated as published, because bios are already public on `/view` | `profile_api.to_profile` |
| contacts | Empty for self and connections ("No contact details added yet"). `None`, so locked, for everyone else. | `profile_api.to_profile` and `get_profile` |
| update endpoint | Edit page previews changes, but its save and publish buttons are disabled | `templates/profile/edit.html` |
| wave endpoints | `sendWave` and `acceptWave` are stubs that send nothing and say so | `static/profile.js` |
| categories endpoint | The idle home page shows random tag groups from `/api/discover` | `static/home.js` |
| category slug | Made from `category_name` | `colours.category_slug` |

`viewer_relation`, `wave_status` and `connection_count` are **derived** from the real
`connections` table (they are not fallbacks).

## Running it locally

There's no separate frontend server, `.env` or CORS setup: Flask serves everything on
one origin.

```bash
pip install flask flask-login flask-sqlalchemy
rm -f instance/app.db          # only if your database predates the tags change
python testdata.py             # optional: 5 seeded users (drops all tables first)
python app.py                  # http://127.0.0.1:5000
```

- **Mac:** port 5000 is taken by AirPlay, so change the port in the last line of
  `app.py`, or turn off AirPlay Receiver.
- **Preview as:** only appears when the app runs with `app.run(debug=True)`.
- **Seeded accounts:** sign in with the user's email and `password123`.
  - Seen from `alex@uni.ac.uk`:
    - **self:** `/u/1`
    - **connection:** `/u/2` (maya), `/u/3` (liam)
    - **other, and has waved at you:** `/u/4` (priya)
    - **other:** `/u/5` (sam)
  - Until problem 1 is fixed, any password works.
