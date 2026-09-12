---
name: scrape-events-digest
description: Fetches today's events from configured sources and texts a digest. Minimal test version — no filtering/formatting polish yet.
---

1. Read the `Sources` table from the connected Airtable base. Use the first row's URL.
2. Fetch that URL and extract any events listed on the page (title, date/time, location, link if available). Don't filter — include everything found.
3. Format a plain-text list of what was found, one line per event.
4. Send that text via the Twilio connector, to the user's own phone number.
5. Write one row to the `EventLog` table in Airtable: date (today), event title/details (from step 2), Sent = true.

This is a minimal end-to-end test — just prove each step works. Real filtering/formatting/relevance logic comes later.
