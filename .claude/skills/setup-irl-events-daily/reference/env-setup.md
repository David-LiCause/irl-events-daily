# Environment variables setup

`.env` holds this project's local credentials/config: `AIRTABLE_PAT`, `AIRTABLE_WORKSPACE_ID`, and `DIGEST_RECIPIENT_EMAIL`. It's gitignored — every clone/fork starts without one, and it never reaches the routine's cloud checkout (see the caveat at the end).

## Requires the user
- **The Airtable PAT:** create it at airtable.com/create/tokens with `data.records:read`, `data.records:write`, `schema.bases:write` scopes — see `reference/airtable-connector-setup.md`. Only the user can create this.
- **Their own email address**, to receive the digest. Ask for it directly — don't guess or infer it.

**Print the PAT-creation step to the user verbatim and wait for them to give you the token value and their email before continuing.**

## What Claude Code handles
1. If `.env` doesn't exist yet, create it by copying `.env.example` (`cp .env.example .env`).
2. Write the user-supplied values into `.env`: `AIRTABLE_PAT`, `AIRTABLE_WORKSPACE_ID`, `DIGEST_RECIPIENT_EMAIL`.
3. Verify all three are non-empty in `.env` before moving on — if any is missing, stop and ask for it rather than proceeding with a gap.

## Caveat: `.env` doesn't reach the scheduled routine
Because `.env` is gitignored, it's never pushed to the remote — the routine's cloud checkout (cloned fresh from the repo on each run) won't have it. `.env` is authoritative for:
- `AIRTABLE_PAT`/`AIRTABLE_WORKSPACE_ID`, used only by the local `make setup-airtable` script (run once, locally, during setup — never inside the routine).
- `DIGEST_RECIPIENT_EMAIL`, used for manual/local test runs of `run-irl-events-daily`.

For the actual scheduled routine, `DIGEST_RECIPIENT_EMAIL`'s value must instead be read out of `.env` here during setup and embedded as a literal in the routine's creation prompt — see `reference/create-routine.md`.
