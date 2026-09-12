# Gmail connector setup

## Requires the user — manual, cannot be done by Claude Code
Connecting a connector always opens an OAuth authorization window that only the user can approve — Claude Code cannot log in or grant consent on the user's behalf.

Go to claude.ai/customize/connectors → connect (or reconnect) **Gmail** → in the authorization window, log in with the Google account and approve **send** scope specifically (not just read) — required so the routine can send the digest.

**Print this step to the user verbatim and wait for confirmation before continuing.**

## What Claude Code can do on its own, once the above is done
- **Verify it's connected with the right scope:** call the Gmail MCP `list_labels` as a basic connectivity check, then confirm send actually works the first time the skill sends an email (a permissions error there means the connector is connected but missing send scope — re-surface the manual step above, don't retry silently).
- Everything after that — sending the daily digest — is fully automatic via the connector.
