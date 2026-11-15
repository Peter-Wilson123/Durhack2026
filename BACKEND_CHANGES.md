# Backend changes (for Craig and Peter)

Small, targeted backend edits made from the frontend side, one commit each, so
any of them can be undone on its own with `git revert <commit>`.

- **No schema changes:** no new, changed or dropped columns or tables.
- **No data changes.**

Each change was tested against a seeded copy of the database (`python testdata.py`)
with Flask's test client. The results are noted under each one.

## SECURITY-RELEVANT (all of these tighten access; none loosens it)

### 1. Only `@durham.ac.uk` addresses can register
- **File:** `app.py`, `register()`
- **What changed:** after the existing checks, an email that doesn't end in `@durham.ac.uk` (any letter case) is refused. The page shows "This site is for Durham students only. Please use your student @durham.ac.uk address." (`templates/register.html` shows it.)
- **Why:** `/register` accepted any domain, so non-Durham people could join.
- **Needed for:** the Durham-students-only rule.
- **Schema:** no. **Security:** yes. It tightens sign-up only.
  - Signing in is unchanged: the seed users have `@uni.ac.uk` addresses and still sign in.
  - It does **not** tell students from staff; that needs real verification (see Gaps).
- **Tested:** `someone@gmail.com` is refused and no account is made; `…@Durham.ac.uk` registers.
- **Undo:** `git revert f7bd510`

### 2. `/update-account` can no longer change the username (CIS code)
- **File:** `user_account.py`, `update_user_account()`
- **What changed:** the `new_username` argument is ignored. Bio and interest updates work as before.
- **Why:** `users.username` is the CIS code people sign in with. Any signed-in user could change theirs to any unused value. That includes taking someone else's CIS code before that person registers.
- **Needed for:** the rule that CIS codes are protected.
- **Schema:** no. **Security:** yes. The `/account` form's username field was removed to match (frontend commit).
- **Tested:** posting `new-username=hijacked` leaves the username as `alex`, and the bio still saves.
- **Undo:** `git revert a0b0b3d`

### 3. Creating an interest needs sign-in
- **File:** `interests.py`, `POST /interests/new`
- **What changed:** added `@flask_login.login_required`, like the other write routes.
- **Why:** signed-out requests could create interests with no creator recorded.
- **Needed for:** create-interest flow security.
- **Schema:** no. **Security:** yes.
- **Tested:** signed out, the request is refused and nothing is created; signed in, the interest is created with `created_by_user_id` set.
- **Undo:** `git revert 2b46eca`

## Other changes

### 4. Registration no longer crashes
- **File:** `app.py`, `register()`
- **What changed:** `auth.load_user()` was called with a `password` argument it doesn't accept, so every sign-up created the account and then failed with a 500 error. The extra argument is removed.
- **Needed for:** the sign-in and registration screens working at all.
- **Schema:** no. **Security:** no. The password is checked by `verify_user()` at sign-in, as before.
- **Tested:** before, status 500 (with the account half-made); after, status 200 and the welcome page.
- **Undo:** `git revert a610551`

### 5. Search results include each interest's own category and score
- **File:** `discovery.py`, `interest_json()` and `group_interests()`
- **What changed:** in `/api/discover` **search** results, each interest also has:
  - `"category"`: its own main category name, or `null` if untagged;
  - `"score"`: the match score `discover()` already computes.

  Additive only. Nothing else in the response changes. The empty-query response and `/api/interests` are untouched.
- **Why:** the homepage groups results into category boxes ranked by match. Before this, it had to guess each interest's category from the tag group it arrived in, and some interests landed in the wrong box.
- **Needed for:** homepage search grouped by category.
- **Schema:** no. **Security:** no new personal data; categories and scores are public.
- **Tested:** `q=print` returns, for example, "3D Printing" with category "Engineering and invention" and a score.
- **Undo:** `git revert 4120c14` (the frontend falls back to its old guess automatically).

## Not changed (too large, unclear, or a teammate's area): Gaps for Craig and Peter

| Gap | Proposal |
|---|---|
| **Staff vs students** and **email verification** | Send a sign-up link or code to the address before the account works. Decide how to tell staff from students (for example, the CIS code format, or a university directory lookup). |
| **CSRF protection** on every POST | Add Flask-WTF's `CSRFProtect` and a token in each form and `fetch`. Every form changes, so this needs agreeing first. |
| **Typos create interests** (`/update-account` `new-interests`) | Only link to existing interests, and send unknown names to the create form instead. Teammates' `/account` page relies on today's behaviour. |
| **`POST /u/<id>/edit` overwrites every field** | Accept partial updates; validate contact formats; return JSON errors. |
| **Ranking rule** (name matches slightly above tag matches) | See `docs/search-ranking-spec.md`: `final = max(name_score, 0.9 * best_tag_score)`; today scores are added together. |
| **Handle, discoverability, account deletion, verified flag** | Each needs a new column or endpoint: an additive schema change for you to agree. |
| **Search JSON includes `tags[]`** | Not shown anywhere in search, but visible in the Network tab. Drop it from search responses if nothing else uses it. |
| **Old product name in the backend** | None found: there is no verification email (subject or sender) and no OpenAPI title. When verification emails are added, use "Durham Superposition". |
| **Seed users have non-Durham addresses** (`@uni.ac.uk`) | Change `testdata.py` to `@durham.ac.uk` if sign-in should also be Durham-only. |
