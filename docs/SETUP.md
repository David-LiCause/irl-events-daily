# Setup

Minimal checklist to stand up the architecture for the first end-to-end test. Expand with full details once the pipeline is validated.

## Connectors (claude.ai/customize/connectors)
- [ ] Twilio — connect.
- [ ] Airtable — connect, select the dedicated base.
- [ ] Google Calendar — already connected; confirm/select the "Events" calendar specifically if a calendar-scoping step is offered (this is one of the open assumptions being tested).

## Google Calendar
- [ ] Create a calendar named "Events" if it doesn't already exist.

## Airtable base
- [ ] Copy `.env.example` to `.env` and fill in `AIRTABLE_PAT` (create at airtable.com/create/tokens with `data.records:read`, `data.records:write`, `schema.bases:write` scopes) and `AIRTABLE_WORKSPACE_ID`.
- [ ] Run `make setup-airtable` — creates the `events-daily` base with `Sources` (Name, URL — one row per org/URL pair) and `EventLog` (Date, DigestIndex, EventTitle, EventDescription, EventTime, Location, Price, SignupURL, SourceName, SourceURL, Sent, AddedToCalendar, CalendarEventId) tables.
- [ ] Add at least one real event-page URL to `Sources` for the first test.

## GitHub App access (per-user — required before creating any routine)
- [ ] Grant Claude's GitHub App access to your copy of this repo: github.com/settings/installations → find the Claude/Claude Code app → Configure → add this repo (or your fork) to its repository access list. Without this, routine creation fails with a 403 permission error.
- [ ] This is tied to your own GitHub account, not the repo itself — if this repo is public and someone else clones/forks it, they must do this same step for their own copy under their own account.

## Routine A — scrape-events-digest
- [ ] Create via the `schedule` skill / RemoteTrigger.
- [ ] Cron trigger (daily).
- [ ] Environment: `full-network-access`.
- [ ] `sources`: this repo.
- [ ] `mcp_connections`: Twilio, Airtable.
- [ ] Prompt: `/scrape-events-digest`.

## Routine B — add-event-to-calendar
- [ ] Needs an API-triggerable routine — confirm this trigger type exists in the claude.ai/code/routines UI (not exposed by the `RemoteTrigger` tool, which only supports cron/run_once_at).
- [ ] `mcp_connections`: Google Calendar, Airtable.
- [ ] Prompt template: `/add-event-to-calendar <reply text>`.

## Twilio Studio (deferred until Routine B is confirmed working standalone)
- [ ] Buy/confirm a phone number.
- [ ] Build Studio Flow: Trigger widget (incoming SMS) → HTTP Request widget → Routine B's API-trigger endpoint.
