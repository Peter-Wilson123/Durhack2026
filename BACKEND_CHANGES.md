# Backend changes (for Craig and Peter)

Small, targeted backend edits made from the frontend side. Each is its own
commit, so it can be undone on its own with `git revert <commit>`.

(An earlier version of this file was removed from `main` in 93910d9. The changes it
listed are in git history: a610551, f7bd510, a0b0b3d, 2b46eca and 4120c14.)

## Title case for new interest names

- **Files:** new `interest_names.py`; `interests.py` (`POST /interests/new`); `user_account.py` (where `/update-account` creates an interest from a name it doesn't know)
- **What changed:** before a **new** interest is saved, its name goes through `to_interest_title_case()`:
  - spaces are trimmed and collapsed;
  - each word gets a capital first letter;
  - words typed in capitals (CS, DNA, D&D) are kept;
  - small words (of, the, and…) stay lowercase inside a name;
  - hyphen, `&` and `/` parts are each capitalised;
  - a word starting with a digit ("1970s", "3d") is kept as typed.

  The browser uses the same rules (`static/titleCase.js`); `tests/title_case_cases.json` is the shared list both are tested against.
- **Why:** so names are consistent, and a direct request can't skip what the create form does.
- **Needed for:** create-interest title case.
- **Duplicate check:** unchanged. It was already case-insensitive (`func.lower`), so "astronomy" finds "Astronomy".
- **Schema:** no. **Data:** no. Existing interests are not renamed.
- **Security:** no.
- **Tested:** `tests/test_title_case.py` (27 shared cases) and `tests/test_backend_changes.py`:
  - a created name is saved in title case;
  - a lowercase duplicate goes to the existing interest and nothing new is created;
  - `/update-account` creates new names in title case.
- **Undo:** `git revert 5975efe 243502d`

## Not changed: Gaps for Craig and Peter

| Gap | Proposal |
|---|---|
| **No edit-interest endpoint** | So there's no rename to apply title case to. When one is added, run the new name through `to_interest_title_case()` and keep the case-insensitive duplicate check. |
| **Existing names that differ from the rules** | Only "Medieval Re-enactment" in the seed data (the rules give "Re-Enactment"). Not renamed; fix it in `taxonomy.py` if wanted. |
| **Search is case-insensitive already** | `discovery.search_interests` lowercases both sides. No change needed. |
| **No interest slugs yet** | When slugs are added, build them from the title-cased name. |
