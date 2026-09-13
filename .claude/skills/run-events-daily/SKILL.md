---
name: run-events-daily
description: Fetches today's events from every configured source, emails the user a full digest with a one-click Google Calendar "Add to Calendar" link per event, and logs the results to Airtable.
---

**This is a prescriptive, step-by-step workflow.** Execute the steps below in order, one at a time — do not skip ahead, reorder, or run steps in parallel. Before moving to the next step, confirm the current one actually completed. If any step is incomplete or cannot be completed (a connector won't connect, a command fails, required info is missing), **stop immediately and flag it to the user** — do not improvise a workaround or continue past it.

1. **Determine today's date.** Resolve the current date in **America/New_York** (not UTC — the cloud environment clock is UTC): run `TZ=America/New_York date +%Y-%m-%d` via Bash. Use this single value for the rest of the run to decide "is this event today."

2. **Pull sources from Airtable.**
   - If you don't already have the `events-daily` base's ID this session, call the Airtable MCP `search_bases` to find it, then `list_tables_for_base(baseId)` to get the `Sources` table's `tableId`.
   - Call `list_records_for_table(baseId, tableId, fields: ["Name", "URL"])` to read rows.
   - This call is paginated — if the response includes a `next_cursor`/offset, keep calling with that cursor until none remains, so **every** row is read, not just the first page.
   - For each record returned, capture `Name` and `URL` from its `fields`.

3. **Iterate sources and extract today's events.** For each `Name`/`URL` pair:
   - Fetch the URL.
   - Extract any events listed on the page (title, date/time, location, signup/details link).
   - Filter to only events matching today's date from step 1 — discard everything else.
   - Attach the source `Name`/`URL` to each surviving event as `SourceName`/`SourceURL`.

4. **Fallback when a source URL doesn't yield a clear events list.** Trigger condition: fetching the URL returns no recognizable events list (page error, redirect, layout the extraction can't parse, or zero events found where that's implausible). Fallback: web-search for the organization's actual current events/calendar page (search on the `Name`) to find a better URL, then retry extraction (step 3) against that URL for this run only. Flag any source where the fallback was used — don't silently overwrite its `Sources` row — and call it out in your final summary at the end of this run so the user knows that source's URL may need updating.

5. **Write the extracted events to `events.json`** (a scratch file in the current working directory): a flat JSON array, one object per event, with these exact fields (matching `EventLog` Airtable columns):
   ```json
   [
     {
       "Date": "YYYY-MM-DD",
       "DigestIndex": null,
       "EventTitle": "string",
       "EventDescription": "string",
       "EventTime": "string",
       "StartDateTime": "YYYY-MM-DDTHH:MM:SS",
       "EndDateTime": "YYYY-MM-DDTHH:MM:SS or null",
       "AllDay": false,
       "Location": "string",
       "Price": "string or null",
       "SignupURL": "string or null",
       "SourceName": "string",
       "SourceURL": "string",
       "Sent": false,
       "AddedToCalendar": false,
       "CalendarEventId": null
     }
   ]
   ```
   - `StartDateTime`/`EndDateTime` are local **America/New_York** time, no offset. `EventTime` stays a human-readable string for display in Airtable.
   - `EndDateTime: null` means "unknown" — `build_digest.py` defaults to a 2-hour duration.
   - `AllDay: true` events omit time-of-day.
   - `DigestIndex`/`Sent`/`AddedToCalendar`/`CalendarEventId` are placeholders at write time — leave them as shown above.

6. **Build the digest.** Run:
   ```
   python3 .claude/skills/run-events-daily/scripts/build_digest.py events.json digest_output.json
   ```
   This validates `events.json`, builds a Google Calendar quick-add URL for each event, and renders the email into `digest_output.json` (`{"subject": ..., "body": ...}`). If it exits non-zero, fix the offending event data in `events.json` and rerun — do not proceed to send with unvalidated data.

7. **Send the email.**
   - Determine the recipient first: if this run's prompt embeds a recipient email (the scheduled routine's prompt does — see `reference/create-routine.md` in the `setup-events-daily` skill), use that address. Otherwise (a manual/local run), read `DIGEST_RECIPIENT_EMAIL` from `.env`. Never fall back to a hardcoded address, and never send anywhere else — this is the project's core safety guarantee (`dev/PRD.md`).
   - Read `digest_output.json` for `subject`/`body`.
   - Call the Gmail MCP `send_message` tool with exactly these parameters:
     ```json
     {
       "to": ["<recipient address from above>"],
       "subject": "<subject from digest_output.json, verbatim>",
       "body": "<body from digest_output.json, verbatim>"
     }
     ```
   - Do not set `cc`, `bcc`, `htmlBody`, `draftId`, or any other parameter. Do not reformat or rewrite `subject`/`body` — send them exactly as written.

8. **Log the run to `EventLog`.** Write one row per event (from `events.json`) to the `EventLog` table via the Airtable connector: same fields, but set `Sent: true` and assign `DigestIndex` as each event's 1-based position in the digest. Leave `AddedToCalendar`/`CalendarEventId` blank — nothing populates them, since adding an event to the calendar happens directly in the user's browser when they click a quick-add link, with no routine involvement.

9. **Prune old `EventLog` rows.** Read all `EventLog` rows via the Airtable connector and delete any whose `Date` is more than 7 days before today's date (from step 1) — this keeps `EventLog` a rolling ~7-day window (see `dev/PRD.md` §6.2). This is routine maintenance, not event dedup, and must not block the digest: if it fails, note that in the final summary rather than retrying or aborting the run.

10. **Report a final summary** to the user: number of sources checked, number of events found, any sources where the step-4 fallback was used (so their `Sources` table URL may need updating), and how many old `EventLog` rows were pruned in step 9.
