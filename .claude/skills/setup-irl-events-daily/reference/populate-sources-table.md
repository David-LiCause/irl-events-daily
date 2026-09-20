# Populate the Sources table

**This is a prescriptive, step-by-step workflow.** Follow the steps in order, iterating step 2 once per org/venue the user gives you. Do not write anything to Airtable until the user has explicitly confirmed the full list in step 4.

1. **Explain the context, then ask for the first org/venue.** Tell the user: the daily routine will fetch each URL they list here, look for events happening that day, and email them a digest of anything it finds — one row per org/venue, each pointing at the page the routine should check. Then ask them to name one organization or venue they want to track, with a URL to its event page if they already have one (a URL is optional — a name alone is enough to start from).

2. **For each org/venue the user gives you, resolve and validate its URL:**
   - **Always fetch the page and inspect the actual content — never judge a URL by domain, title, or search snippet alone.** This applies to a URL the user gives you and to any candidate you find via search.
   - **If they gave a URL:** fetch it and check the content shows a real events list (titled events with dates — not a homepage, ticket-purchase page, or dead link). If it does, keep it. If not, tell the user what you actually found, then search for the org's real events page and validate each candidate the same way before proposing one.
   - **If they gave only a name:** search for the org's events page, fetch and validate each candidate, and propose the best match.
   - Show the user the URL you settled on plus a one-line note on what you saw on the page confirming it's an events list, before moving to the next org.
   - Multiple relevant URLs for one org become multiple rows (same `Name`, different `URL`) — validate each individually.
   - **Ask whether they want any source-specific instructions for this org/venue** — e.g. events to always filter out ("skip anything Mon–Fri between 9 AM and 5 PM") or to keep ("only keep hikes"). This is optional; most sources have none. If they give one, restate it back in explicit terms (days, times, keywords — America/New_York) so it can't be misread, and record it as this row's `Instructions`. Leave it empty otherwise.

3. **Ask if there's another org/venue to add**, and repeat step 2 for it. Keep looping until the user says they're done — this list is expected to have multiple entries.

4. **Confirm the complete list back to the user before writing anything.** Show every org/venue with the final URL(s) and any `Instructions` you'll be using for each, exactly as they'll be written to Airtable, and ask for explicit confirmation. If the user wants changes, make them and re-confirm — do not proceed to step 5 on an implicit or partial yes.

5. **Write one row per org/URL pair** via the Airtable connector (`Name`, `URL`, and `Instructions` columns — leave `Instructions` empty when there are none) — only after step 4's confirmation.

6. **Read the table back and show the user the final row count/contents** to verify the writes match what was confirmed.
