---
name: add-event-to-calendar
description: Parses an SMS reply and creates the matching event on the Events calendar. Minimal test version — trivial matching, no polish yet.
---

Takes the user's reply text as an argument.

1. Read the most recent row(s) from the `EventLog` table in Airtable.
2. Match the reply text to one of those rows. For this initial test there's only ~1 candidate event, so trivial matching is fine.
3. Create that event on the Google Calendar named "Events" (not any other calendar).
4. Update that row in `EventLog`: AddedToCalendar = true.

This is a minimal end-to-end test — just prove each step works. Real reply-parsing/matching logic comes later.
