# Setup

Minimal checklist to stand up the architecture for the first end-to-end test. Expand with full details once the pipeline is validated.

## Connectors (claude.ai/customize/connectors)
- [ ] Airtable — connect, select the dedicated base.
- [ ] Gmail — connect (or reconnect) with **send** scope. The routine needs this to email the digest — a previous, more conservative design kept Gmail read-only-only; that's been revised since the routine only ever sends to the user's own address (see `dev/PRD.md` §6.4).
- [ ] Google Calendar connector is **not needed** for this routine — the calendar write happens client-side (the user clicks a quick-add link in their own browser), not via any connector.

## Google Calendar
- [ ] Create a calendar named "Events" if it doesn't already exist — this is what the user selects from the calendar dropdown when saving an event via a quick-add link.

## Airtable base
- [ ] Copy `.env.example` to `.env` and fill in `AIRTABLE_PAT` (create at airtable.com/create/tokens with `data.records:read`, `data.records:write`, `schema.bases:write` scopes) and `AIRTABLE_WORKSPACE_ID`.
- [ ] Run `make setup-airtable` — creates the `events-daily` base with `Sources` (Name, URL — one row per org/URL pair) and `EventLog` (Date, DigestIndex, EventTitle, EventDescription, EventTime, Location, Price, SignupURL, SourceName, SourceURL, Sent, AddedToCalendar, CalendarEventId) tables.
- [ ] Add at least one real event-page URL to `Sources` for the first test.

## GitHub App access (per-user — required before creating any routine)
- [ ] Grant Claude's GitHub App access to your copy of this repo: github.com/settings/installations → find the Claude/Claude Code app → Configure → add this repo (or your fork) to its repository access list. Without this, routine creation fails with a 403 permission error.
- [ ] This is tied to your own GitHub account, not the repo itself — if this repo is public and someone else clones/forks it, they must do this same step for their own copy under their own account.

## Routine — scrape-events-digest
- [ ] Create via the `schedule` skill / RemoteTrigger.
- [ ] Cron trigger (daily).
- [ ] Environment: `full-network-access`.
- [ ] `sources`: this repo.
- [ ] `mcp_connections`: Airtable, Gmail.
- [ ] Prompt: `Read the file .claude/skills/scrape-events-digest/SKILL.md in this repo and carry out the instructions in it exactly.` (skill slash-commands don't work in routine sessions — see `dev/TECHNICAL_DESIGN.md` Findings.)

No second routine, no reply bridge, no SMS provider of any kind is needed in this design — the calendar write happens directly in the user's browser when they click a quick-add link in the email.
