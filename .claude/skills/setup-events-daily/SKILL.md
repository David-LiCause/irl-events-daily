---
name: setup-events-daily
description: One-time setup for events-daily — verifies/creates the Airtable base and tables, confirms connector configuration, ensures the "Events" Google Calendar exists, and seeds the Sources table with at least one event-page URL. Run once before the first run-events-daily routine execution.
---

1. Confirm `.env` has `AIRTABLE_PAT` and `AIRTABLE_WORKSPACE_ID` set (see `.env.example` for where to find each). If either is missing, ask the user for it before continuing.
2. If the `events-daily` Airtable base doesn't already exist, run `make setup-airtable`. This creates the base with a `Sources` table (Name, URL) and an `EventLog` table (Date, DigestIndex, EventTitle, EventDescription, EventTime, Location, Price, SignupURL, SourceName, SourceURL, Sent, AddedToCalendar, CalendarEventId). Confirm the base and both tables exist before moving on.
3. Confirm connectors are attached at claude.ai/customize/connectors:
   - **Airtable** — connected, with the `events-daily` base selected.
   - **Gmail** — connected with **send** scope (needed to email the digest; see `dev/PRD.md` §6.4 for why this scope is accepted for this project).
   - **Google Calendar** connector is **not** needed — the calendar write happens client-side when the user clicks a quick-add link in the email, not via any connector.
   If anything is missing, tell the user exactly what to do and stop here — don't proceed to routine creation without all of the above in place.
4. Confirm a Google Calendar named "Events" exists in the user's Google Calendar. If not, ask the user to create one — this is what they'll select from the dropdown when saving an event via a quick-add link.
5. Confirm the `Sources` table has at least one row (`Name`, `URL` — one row per org/URL pair; an org with multiple relevant pages gets multiple rows sharing the same `Name`). If it's empty, ask the user for one real event-page URL and add it as a row.
6. Confirm Claude's GitHub App has access to this repo: github.com/settings/installations → the Claude/Claude Code app → Configure → add this repo (or the user's fork) to its repository access list. This is tied to the user's own GitHub account, not the repo itself, and is required before creating any routine — without it, routine creation fails with a 403.
7. Tell the user setup is complete, and that they can now create the `run-events-daily` routine:
   - Cron trigger, daily.
   - Environment: `full-network-access`.
   - `sources`: this repo.
   - `mcp_connections`: Airtable, Gmail.
   - Prompt: "Read the file `.claude/skills/run-events-daily/SKILL.md` in this repo and carry out the instructions in it exactly." (Skill slash-commands don't resolve inside routine sessions, so the prompt must point at the file directly rather than invoking the skill by name.)

This is one-time setup — re-run it only if connectors are reconnected, the Airtable base is recreated, or a fresh copy of this repo needs its own GitHub App access grant.
