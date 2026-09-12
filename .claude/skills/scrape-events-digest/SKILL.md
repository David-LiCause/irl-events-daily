---
name: scrape-events-digest
description: Fetches today's events from configured sources and emails the user a digest with a one-click Google Calendar "Add to Calendar" link. Proof-of-concept version — single representative event only, no full digest formatting/polish yet.
---

1. Read the `Sources` table from the connected Airtable base. Use the first row's URL.
2. Fetch that URL and extract any events listed on the page (title, date/time, location, link if available). Don't filter — include everything found.
3. Pick ONE representative event from what you found in step 2 (e.g. the first one with a clear date/time) to use as this proof-of-concept's test event. (A full digest covering every event found — one link per event, nicer formatting — is deferred; see the note at the end of this file.)
4. For that one event, build a Google Calendar "quick add" URL in this exact format:
   `https://www.google.com/calendar/render?action=TEMPLATE&text=EVENT_TITLE&dates=START/END&details=DESCRIPTION&location=LOCATION&ctz=America/New_York`
   - `text`, `details`, and `location` must be URL-encoded.
   - `dates` uses `YYYYMMDDTHHMMSS/YYYYMMDDTHHMMSS` (timed events) or `YYYYMMDD/YYYYMMDD` (all-day) in `America/New_York` local time — do not convert to UTC.
   - If the event's end time isn't known, assume a 2-hour duration.
   - Include the original event page/signup link (if found in step 2) inside `details`, alongside a short description, so the user has a way back to the source.
5. Send an email via the Gmail connector to licausedavid@gmail.com with:
   - Subject: e.g. "Events Daily (test): <event title>"
   - Body (plain text is fine for this proof of concept): the event's title, date/time, location, and the quick-add URL from step 4 as a plain clickable link.
6. Write one row to the `EventLog` table in Airtable: Date (today), EventTitle/EventDescription/EventTime/Location/SignupURL (from step 2's data for the chosen event), SourceName/SourceURL, Sent = true. Leave `AddedToCalendar` and `CalendarEventId` blank — nothing populates them anymore, since adding the event to the calendar now happens directly in the user's browser when they click the link, with no routine involvement.

This is a minimal end-to-end proof of concept for the email + quick-add-link mechanism only: one event, one link, plain-text email. NOT yet built (deferred to a later round): a full digest covering every event found on the page, one quick-add link per event, and better visual/HTML formatting.
