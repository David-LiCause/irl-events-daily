# events-daily

Every day, a Claude Code Routine checks a list of event pages (kept in an Airtable `Sources` table) and emails the user a digest of that day's events, each with a one-click Google Calendar "quick add" link. Adding an event to the calendar happens in the user's own browser when they click a link — no routine ever writes to the calendar directly. See `dev/PRD.md` for the full problem statement and technical design.

Setting up a fresh copy of this repo? Run the `setup-events-daily` skill (`.claude/skills/setup-events-daily/SKILL.md`) first — it walks through the Airtable base, connectors, and calendar prerequisites the daily routine needs.
