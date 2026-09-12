# events-daily

## 1. Problem Statement
Event pages for organizations/venues the user follows have no easy calendar export. Keeping up with what's happening requires manually checking many different sites. There's no single feed to subscribe to.

## 2. Goal
Every day, automatically check a list of event pages and text the user a summary of events happening **that day**. The user can reply to the text to add a specific event to their Google Calendar.

## 3. Success Criteria
- A text arrives daily with that day's relevant events, pulled from the configured source pages.
- Replying to the text adds the chosen event to the user's calendar without opening a browser.
- No unintended side effects, specifically:
  - No text messages are ever sent to anyone other than the user.
  - No emails are ever sent, drafted, replied to, or forwarded on the user's behalf.
  - No calendar writes (create/update/delete) occur on any calendar other than the one designated "Events" calendar.
  - No events are added to the calendar that the user didn't explicitly approve via their reply.

## 4. Non-Goals (v1)
- No deduplication / history tracking — each day's digest is self-contained (today's events only), so there's nothing to dedupe against.
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
- Official Twilio MCP connector exists for SMS — no custom hosting needed for messaging.

### 6.2 Components
1. **Source list** — a maintained list of event page URLs (start with 3–5 sites).
2. **Routine A (scheduled trigger)** — fetches each source page, extracts today's events (title, time, location, link) via prompt, filters by relevance/interest, formats a digest, and sends it via the **Twilio MCP connector** (official Twilio-Claude integration, installed via Claude Code `/plugins` → `twilio-developer-kit`, or Connectors directory).
3. **Twilio Studio Flow** — receives the user's inbound SMS reply and forwards it (via an HTTP Request widget) to Routine B's API-trigger endpoint. Inbound handling lives here, not in the MCP connector.
4. **Routine B (API trigger)** — fires on the Studio Flow's request, parses the freeform reply text to identify the intended event, and creates it on a single, dedicated Google Calendar (e.g., "Events").
5. **Connectors used:**
   - **Google Calendar** — attached only to Routine B; scoped as narrowly as possible while still allowing event creation. (See open question on single-calendar restriction.)
   - **Gmail** — optional in v1, not required for the core loop (no email-sourced events planned yet). If added later, connect as `gmail.readonly` only — never grant send/draft/trash scopes.
   - **Twilio** — attached only to Routine A, for sending the digest. Inbound replies are handled by the Studio Flow, not this connector.

### 6.3 Data flow
**Digest (daily, scheduled):**
```
Routine fires (cron) 
  → browse each source URL 
  → extract today's events 
  → filter by relevance 
  → format message 
  → Twilio connector sends SMS
```

**Reply (event-driven):**
```
User replies to SMS 
  → Twilio Studio Flow: Trigger widget fires on the incoming message 
  → Studio Flow: Make HTTP Request widget POSTs to Routine B's API-trigger endpoint 
    (with Authorization bearer token + anthropic-beta header, reply text as freeform payload) 
  → Routine B fires as a new, independent autonomous session 
  → Routine B's prompt parses the freeform reply text to identify which event was meant 
  → Calendar connector creates event on the dedicated "Events" calendar
```

The Twilio Studio Flow is the bridge between the inbound SMS and the routine — it's a no-code flow built entirely within the existing Twilio account (drag-and-drop, two widgets), not a separately hosted service. Free for the first 1,000 executions/month ($0.0025/execution after), which comfortably covers daily use.

**Important architectural note:** this is deliberately **two separate routines**, not one paused mid-run:
- **Routine A** (scheduled trigger): sends the daily digest.
- **Routine B** (API trigger only): performs the calendar write, and only has the Calendar connector attached (not Gmail, not Twilio-send) to limit what it's capable of.

This is required because Claude Code Routines run fully autonomously with **no approval prompts and no way to pause for human input mid-run** (confirmed in Anthropic's docs: "there is no permission-mode picker and no approval prompts during a run"). A routine cannot send a notification and wait for a tap/reply itself. The human-in-the-loop effect instead comes from Routine B simply never running until the user's SMS reply triggers it externally — the "approval" is that nothing happens without that reply, not an in-run confirmation step. (This also means a mobile push-notification/approve-in-app flow, which relies on interactive Remote Control sessions, is not compatible with routines and was ruled out as an alternative.)

### 6.4 Permissions & security model
- **Principle:** since routines run with no approval prompts and use every tool of every attached connector automatically, OAuth scope + which connectors are attached to which routine are the *only* real enforcement boundaries — not runtime confirmation.
- **Calendar:** connect with the narrowest scope that still allows event creation; direct all writes to one dedicated calendar, not the user's primary calendar. Only Routine B (calendar write) has this connector attached — Routine A (digest) does not need it.
- **Gmail (if/when added):** `gmail.readonly` only. Never connect send/draft-capable scopes. Not attached to either routine in v1.
- **Twilio:** credentials via the official connector's own credential handling (not a self-managed flat file). Only Routine A (digest) needs send capability; Routine B doesn't need Twilio at all.
- No AWS/EC2, no self-hosted credential store, no general-purpose "hands on the machine" agent framework (i.e., not OpenClaw) — smaller surface area by design.

### 6.5 Hosting
None required. The digest flow runs fully on Claude's managed infrastructure. The reply→calendar-write path uses a Twilio Studio Flow (native, no-code, within the existing Twilio account) as the bridge — no separately hosted server or custom bridge component needed.

### 6.6 Cost
- Claude Pro: $20/mo (existing plan) — expected to cover 1 routine run/day comfortably.
- Twilio: ~$1–2/mo number rental + ~$0.0079/SMS — negligible at this volume.
- Twilio Studio: free for the first 1,000 flow executions/month, $0.0025/execution after — negligible at one reply/day.
- No AWS/hosting cost under this design.

---

## 7. Open Questions
1. ~~**Reply-trigger bridge**~~ — **Resolved:** use a Twilio Studio Flow (Trigger widget on incoming SMS → Make HTTP Request widget posting to the routine's API-trigger endpoint). Native to Twilio, no custom code or hosting. Still to confirm in practice: the exact request format/headers the routine's API trigger expects, and that Studio's HTTP Request widget can supply them correctly.
2. **Single-calendar restriction:** Google's Calendar OAuth scopes are not restricted to one calendar by default (`calendar`/`calendar.events` grant access across all calendars on the account). Need to check, at connector setup time in Claude's Settings → Connectors, whether there's a calendar-selection step that limits access to just the one dedicated calendar — this wasn't confirmed in research.
3. ~~**Approval-gate behavior in unattended routines**~~ — **Resolved:** confirmed via Anthropic's docs that routines never pause for approval during a run (no permission prompts at all). Design updated to use two separate routines (digest vs. calendar-write), where Routine B only ever runs when triggered by the user's reply — that external trigger is the safeguard, not an in-run approval step. A mobile push-notification/tap-to-approve flow was considered and ruled out: it depends on interactive Remote Control sessions, which routines are not.
4. **Source list format/location:** not yet decided where the list of event page URLs lives (repo file vs. routine config).
