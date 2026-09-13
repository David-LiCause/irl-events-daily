# irl-events-daily

## 1. Problem Statement
Event pages for organizations/venues the user follows have no easy calendar export. Keeping up with what's happening requires manually checking many different sites. There's no single feed to subscribe to.

## 2. Goal
Every day, automatically check a list of event pages and email the user a summary of events happening **that day**, with a one-click Google Calendar "quick add" link to add any event of interest.

## 3. Success Criteria
- An email arrives daily with that day's relevant events, pulled from the configured source pages.
- Clicking a quick-add link in the email opens Google Calendar pre-filled with that event's details, ready to save with one more click.
- No unintended side effects, specifically:
  - No emails are ever sent to anyone other than the user's own address.
  - No calendar writes occur via any Claude routine — writes happen only in the user's own browser session when they click a link.
  - No calendar writes (create/update/delete) occur on any calendar other than the one designated "Events" calendar.
  - No events are added to the calendar that the user didn't explicitly click to add.

## 4. Non-Goals (v1)
- No deduplication of events across days — each day's digest is self-contained (today's events only). A rolling log is kept (see §6.2) for context/audit, but it does not feed back into filtering what's shown in future digests.
- No multi-user support.
- No public distribution / skill marketplace packaging.
- No non-Google calendar support.

## 5. User
Single user (the project owner). Personal Gmail account and Google Calendar.

---

## 6. Technical Design

### 6.1 Platform decision
Built on **Claude Code Routines** (Anthropic's scheduled cloud agents) rather than self-hosting (e.g., OpenClaw on AWS). Rationale:
- No server to run, patch, or secure.
- First-party connectors (Gmail, Google Calendar) enforce OAuth scopes as a hard ceiling at Google's level — not just a prompt-level restriction.
- Fits within the existing $20/mo Claude Pro plan (routines: ~5/day limit on Pro, this project needs 1/day).

### 6.2 Components
1. **Data store (Airtable)** — holds all personal/user-specific data, kept out of the (public) repo entirely:
   - **Sources table** — org/group name → event page URL. Editable directly in Airtable as the source list changes over time.
   - **Event log table** — rolling ~7-day log of events recommended in each day's digest, kept for context/audit (not used for dedup — see §4). The `AddedToCalendar`/`CalendarEventId` fields are currently vestigial — nothing populates them, since the calendar write now happens client-side (see #3 below), not via any routine.
   - Accessed via the official **Airtable MCP connector** (read/write). Scope is limited to the one dedicated base via OAuth base-selection at connector setup.
2. **Single routine (scheduled trigger)** — reads the sources table, fetches each source page, extracts today's events (title, time, location, link) via prompt, builds a Google Calendar "quick add" URL for the event(s), formats an email digest, sends it via the **Gmail MCP connector**, and logs the recommended events to the event log table.
3. **Google Calendar quick-add link** — each event in the email includes a link in the form `https://www.google.com/calendar/render?action=TEMPLATE&text=...&dates=...&details=...&location=...`. Clicking it opens Google Calendar in the user's own browser, pre-filled with the event's details; the user picks the "Events" calendar and clicks Save. This is a stable, public Google feature — no OAuth, no API key, and no Claude routine involvement in the actual calendar write.
4. **Connectors used:**
   - **Gmail** — attached to the routine, with **send** scope (needed to email the digest). This is a deliberate change from an earlier, more conservative design that avoided any send-capable scope — the safeguard is now prompt-level (the routine is only ever instructed to send to the user's own address), not OAuth-level.
   - **Airtable** — attached to the routine, for the sources table and event log (see #1 above).
   - **Google Calendar** — not attached to any routine. The calendar write is entirely client-side (see #3), which removes the OAuth-scope risk this connector used to carry entirely.

### 6.3 Data flow
```
Routine fires (cron)
  → Airtable connector reads sources table
  → browse each source URL
  → extract today's events
  → build a Google Calendar quick-add link for the event(s)
  → format email digest
  → Gmail connector sends the email to the user's own address
  → Airtable connector logs the recommended event(s) to the event log table
```
The user then opens the email and clicks a quick-add link to add any event they want — this step happens entirely in their own browser, with no routine, webhook, or second automated step involved.

### 6.4 Permissions & security model
- **Principle:** since routines run with no approval prompts and use every tool of every attached connector automatically, OAuth scope + which connectors are attached to which routine are the *only* real enforcement boundaries — not runtime confirmation.
- **Calendar:** no routine holds this connector at all — the write happens only in the user's own browser session when they click a quick-add link, which is a stronger safeguard than any OAuth scope could be.
- **Gmail:** needs send scope now (see §6.2). The safeguard is prompt-level (hardcoded self-recipient in the skill instructions), not OAuth-level — this is a residual risk worth tracking, similar in kind to the calendar-scoping question in §7.
- **Airtable:** OAuth-scoped to a single dedicated base at connector setup. Keeps all personal data (source list, event log) out of the public repo entirely.
- No AWS/EC2, no self-hosted credential store, no general-purpose "hands on the machine" agent framework (i.e., not OpenClaw) — smaller surface area by design.

### 6.5 Hosting
None required. The whole flow — scrape, build links, email — runs inside a single Claude Code Routine on Claude's managed infrastructure. There is no bridge component, webhook, or second routine of any kind.

### 6.6 Cost
- Claude Pro: $20/mo (existing plan) — expected to cover 1 routine run/day comfortably.
- Airtable: free tier ($0/mo) — well within limits at this volume (1,000 records/base, 1,000 API calls/month; usage here is ~5–10 calls/day, ~150–300/month).
- No SMS/messaging provider cost, no AWS/hosting cost under this design.

---

## 7. Open Questions
1. ~~**Reply-trigger bridge**~~ — **Moot.** There is no reply step and no second routine anymore — the calendar write happens when the user clicks a quick-add link in their own browser, not via any inbound-message bridge.
2. **Calendar-selector at quick-add time:** Google's quick-add UI shows a calendar-selector dropdown before saving, but there's no URL parameter to preselect "Events" — the user must pick it manually each time. Need to verify this in practice and consider a one-line reminder in the email body ("remember to select the Events calendar").
3. ~~**Approval-gate behavior in unattended routines**~~ — **Moot.** There's no calendar-write routine to gate anymore; the human-in-the-loop step is now the user clicking a link, which is inherently an explicit action, not something a routine could do unattended.
4. ~~**Source list format/location**~~ — **Resolved:** Airtable (sources table), not the repo. Keeps personal data out of the public repo — a repo file would either be public (unacceptable) or gitignored, which doesn't work anyway since a routine's cloud checkout only reflects what's actually pushed to the remote, not local-only files.
5. **Full digest formatting (deferred):** the current proof of concept emails only one representative event. Building the real digest — every event found, one quick-add link each, better visual formatting — is intentionally deferred to a later round.
6. **Vestigial Airtable fields:** `AddedToCalendar`/`CalendarEventId` on `EventLog` are no longer populated by anything. Left in place for now; revisit whether to remove them once the design has settled.
