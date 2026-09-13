# Technical Design — events-daily

See `PRD.md` for full context. This doc outlines the build steps.

Current status: working implementation with email process

## Task 1: Create `setup-events-daily` skill

### 1.0 Skill file + folder structure
```
.claude/skills/setup-events-daily/
  SKILL.md                              — orchestrator only (see below)
  reference/
    airtable-connector-setup.md         — step A
    gmail-connector-setup.md            — step B
    populate-sources-table.md           — step C
    create-routine.md                   — step D
```

`SKILL.md` itself stays thin: a prescriptive, numbered step-by-step process, where each step is a one-line instruction plus a pointer to its reference file for the actual how-to. Sketch of its contents:

1. Check Airtable connector access (list bases via the Airtable connector). If missing, follow `reference/airtable-connector-setup.md`, then return here.
2. Check Gmail connector access (list labels via the Gmail connector). If missing, follow `reference/gmail-connector-setup.md`, then return here.
3. Check whether the `events-daily` Airtable base already has `Sources`/`EventLog` tables. If not, run `make setup-airtable` (see `reference/airtable-connector-setup.md` for the idempotency caveat).
4. Populate the `Sources` table — follow `reference/populate-sources-table.md`.
5. Create the Claude Code routine — follow `reference/create-routine.md`.
6. Report a final summary to the user: connectors confirmed, tables created, source count, routine ID/link.

### 1.1 `reference/airtable-connector-setup.md`
- Go to claude.ai/customize/connectors → connect **Airtable** → select (or create) the base to scope it to.
- Once connected, run `make setup-airtable` (creates the `events-daily` base with `Sources`/`EventLog` tables).
- Idempotency caveat: `scripts/setup_airtable.py` always creates a *new* base — it has no check for an existing `events-daily` base/tables. Before running it, check (via the Airtable connector) whether a base with those tables already exists, to avoid creating duplicates.

### 1.2 `reference/gmail-connector-setup.md`
- Go to claude.ai/customize/connectors → connect (or reconnect) **Gmail** with **send** scope — required so the routine can send the digest.

### 1.3 `reference/populate-sources-table.md`
1. Ask the user for their list of orgs/venues to track, each with one or more event-page URLs.
2. Confirm the parsed list back to the user (org name → URL(s)) before writing anything.
3. Write one row per org/URL pair via the Airtable connector (`Name`, `URL` columns).
4. Read the table back and show the user the final row count/contents to verify.

### 1.4 `reference/create-routine.md`

- **Prerequisite (manual, one-time):** grant Claude's GitHub App access to this repo at github.com/settings/installations → find the Claude/Claude Code app → Configure → add this repo. Without this, routine creation fails with a 403.
- **Creation is not scriptable/Makefile-able.** Routines are created through the `RemoteTrigger` tool inside a Claude Code session — its OAuth token is injected in-process and is never exposed for a standalone script (e.g. `curl`) to use. So this step is: open a Claude Code session and ask it to create the routine (it will load the `schedule` skill and call `RemoteTrigger`), not `make create-routine`.
- **Exact `RemoteTrigger` call** (`action: "create"`), with every parameter and value fixed for this project:

  ```json
  {
    "name": "events-daily",
    "cron_expression": "0 11 * * *",
    "enabled": true,
    "mcp_connections": [
      {
        "connector_uuid": "20dc92c1-0069-4b76-98b8-11d5dbb18499",
        "name": "Airtable",
        "url": "https://mcp.airtable.com/mcp"
      },
      {
        "connector_uuid": "c8caf0b0-df1d-47a4-92b4-2bac6abd062a",
        "name": "Gmail",
        "url": "https://gmailmcp.googleapis.com/mcp/v1"
      }
    ],
    "job_config": {
      "ccr": {
        "environment_id": "env_01GHncgVoYnpHPK16P34rD5Z",
        "session_context": {
          "model": "claude-sonnet-5",
          "sources": [
            {"git_repository": {"url": "https://github.com/David-LiCause/events-daily"}}
          ],
          "allowed_tools": ["Bash", "Read", "Write", "Edit", "Glob", "Grep"]
        },
        "events": [
          {"data": {
            "uuid": "<generate a fresh lowercase v4 uuid>",
            "session_id": "",
            "type": "user",
            "parent_tool_use_id": null,
            "message": {
              "role": "user",
              "content": "Read the file .claude/skills/scrape-events-digest/SKILL.md in this repo and carry out the instructions in it exactly."
            }
          }}
        ]
      }
    }
  }
  ```

  - `environment_id` = `env_01GHncgVoYnpHPK16P34rD5Z` is the **full-network-access** environment (required per `docs/SETUP.md`).
  - `cron_expression` is UTC; `"0 11 * * *"` = 7am America/New_York (confirm DST offset at creation time — routines have a 1-hour-minimum interval, no sub-hourly schedules).
  - `mcp_connections[].name` must match `[a-zA-Z0-9_-]` only — `Airtable`/`Gmail` already satisfy this.
  - Connector UUIDs/URLs above are specific to this user's claude.ai account; re-fetch them via the `schedule` skill if they ever need to be re-verified.
  - After creation, save the returned routine ID / `https://claude.ai/code/routines/{id}` link for reference.

## Task 2: Revise `scrape-events-digest` skill → rename to `run-events-daily`

### 2.1 Determine today's date
- First step of the skill, before touching Airtable or any source: resolve the current date in **America/New_York** (not UTC — the routine's cloud environment clock is UTC, and event filtering/quick-add dates must be local time, per `dev/PRD.md` §6.3-6.4 conventions).
- Carry this date through the rest of the run as the single value used to decide "is this event today."

### 2.2 Pull sources from Airtable
- Read **every** row of the `Sources` table via the Airtable connector (the old PoC only used the first row — this is the full-digest version, so all rows are in scope).
- For each row, capture `Name` and `URL`.

### 2.3 Iterate sources and extract today's events
For each `Name`/`URL` pair:
1. Fetch the URL.
2. Extract any events listed on the page (title, date/time, location, signup/details link).
3. Filter to only events matching the date from 2.1 — discard everything else.
4. Attach the source `Name`/`URL` to each surviving event (needed for the digest and `EventLog`).

### 2.4 Fallback when a source URL doesn't yield a clear events list
- Trigger condition: fetching the URL returns no recognizable events list (page error, redirect, layout the extraction can't parse, or zero events found where that's implausible).
- Fallback: search for the organization's actual current events/calendar page (web search on the `Name`) to find a better URL, then retry extraction (2.3) against that URL for this run.
- Flag any source where the fallback was used in the final output, so the user knows the `Sources` table URL for that org may need updating — don't silently overwrite the Airtable row.

### 2.5 Write the extracted events to a structured JSON file
After 2.3/2.4, the skill writes its findings to `events.json` (scratch file, e.g. in the session workdir): a **flat JSON array**, one object per event, field names matching the `EventLog` Airtable columns exactly (each object = one future `EventLog` row):

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
- `StartDateTime`/`EndDateTime`/`AllDay` are **new** `EventLog` columns (not in the current schema) added specifically to give `build_digest.py` structured data to build the quick-add link from — `EventTime` stays as-is, a human-readable string, for display in Airtable. Add these 3 fields to `scripts/setup_airtable.py`'s `EventLog` field list and to the table list in `docs/SETUP.md`.
- `StartDateTime`/`EndDateTime` are local **America/New_York** time, no offset (matches the quick-add link format's `ctz=America/New_York`).
- `EndDateTime: null` means "unknown" — the script defaults to a 2-hour duration (per the existing quick-add rule).
- `AllDay: true` events omit time-of-day; the script emits `YYYYMMDD/YYYYMMDD` dates instead of the timed format.
- `DigestIndex`/`Sent`/`AddedToCalendar`/`CalendarEventId` are placeholders at write time (`Sent` flips to `true`, `DigestIndex` gets assigned in 2.7 after the email actually sends; `AddedToCalendar`/`CalendarEventId` stay blank — vestigial, per `dev/PRD.md` §7.6).

### 2.6 `scripts/build_digest.py` — validate, build links, render the email
New folder: `.claude/skills/run-events-daily/scripts/build_digest.py`. Run as `python3 scripts/build_digest.py events.json digest_output.json`.

1. **Validate** `events.json` against the 2.5 schema — required fields present (`EventTitle`, `Location`, `SourceName`, `SourceURL`, `StartDateTime`, `AllDay`, at minimum), `Date`/`StartDateTime`/`EndDateTime` parseable, `AllDay` boolean. Fail loudly (non-zero exit, clear message naming the bad event/field) so the skill can fix and rerun rather than silently sending a broken email.
2. **Build the Google Calendar quick-add URL** for each event from `StartDateTime`/`EndDateTime`/`AllDay`, per the existing format (`action=TEMPLATE&text=...&dates=...&details=...&location=...&ctz=America/New_York`), URL-encoding `text`/`details`/`location`. This moves that logic out of the prompt and into deterministic code.
3. **Render the email**:
   - Subject: e.g. `Events Daily: <Date> — N event(s) found`.
   - Body (plain text): one block per event — `EventTitle`, `EventTime`, `Location`, `Price` (if present), the quick-add link, and `SignupURL`/`SourceURL`.
4. **Write output** to `digest_output.json`: `{"subject": "...", "body": "..."}` — JSON (not markdown) so the skill reads two exact string fields with no rendering/parsing ambiguity.

### 2.7 Send the email
The skill reads `digest_output.json` and sends its `subject`/`body` **verbatim** via the Gmail connector to licausedavid@gmail.com — no reformatting or rewriting by the model at this step. Then log the run to `EventLog` as in the existing PoC (Task 2 predates this doc's `Sources`/`EventLog` schema, which is unchanged).

## Task 3: Update the README (keep this very concise)
After cloning the repo:
1. Invoke the `setup-events-daily` skill and follow it through (connectors, tables, sources, routine creation).
2. In Claude Code, manually trigger the routine once to confirm it runs end-to-end.