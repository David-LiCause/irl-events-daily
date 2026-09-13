# Create the daily routine

## Requires the user — manual, cannot be done by Claude Code
**If this is not the user's own original repo, they must fork it first**, then connect *their fork* to Claude's GitHub App, one time per GitHub account: github.com/settings/installations → find the Claude/Claude Code app → Configure → add their fork to its repository access list. A non-owner cannot grant the App access to someone else's repo (e.g. the upstream `David-LiCause/events-daily`) — only to a repo they themselves own, which means forking first if they're not the original owner. Without this, routine creation fails with a 403.

**Print this step to the user verbatim and wait for confirmation before continuing** — Claude Code has no way to grant its own GitHub App access.

Before proceeding, sanity-check that this local checkout is actually pointed at the repo the user just granted access to: run `git remote get-url origin` and confirm it matches. If it still points at the original upstream repo while the user forked and granted access to a *different* URL, stop and flag this — the routine will fail to clone otherwise.

## What Claude Code handles
Everything below happens in-session with the `RemoteTrigger` tool (`action: "create"`) — it can't be scripted outside a live session, since `RemoteTrigger`'s OAuth token is injected in-process and never exposed to a standalone script.

**Four values below are account/fork-specific and must be resolved fresh each time — never reuse a value seen in a previous run, a doc, or another account's setup:**

1. **Repo URL:** the `git remote get-url origin` value confirmed above — use it for `session_context.sources[].git_repository.url`. Do not assume any specific owner/repo.
2. **Connector UUIDs for Airtable and Gmail:** each claude.ai account gets its own connector UUID per OAuth connection when it connects a connector — look these up for the *current* account via the `schedule` skill. Never hardcode or carry over a UUID from a different account's setup.
3. **`environment_id` for the full-network-access environment:** same caveat as #2 — resolve it for the current account via the `schedule` skill rather than assuming a fixed literal.
4. **Digest recipient email:** read `DIGEST_RECIPIENT_EMAIL` from `.env` (set up in `reference/env-setup.md`) and embed it as a literal in the routine's prompt (see `events` below) — the routine's cloud checkout won't have `.env` at run time since it's gitignored, so this is the only way the scheduled routine gets this value.

Everything else below is a fixed, universal constant — safe to reuse as-is regardless of account or fork:

| Parameter | Value |
|---|---|
| `name` | `"events-daily"` |
| `cron_expression` | `"0 11 * * *"` (UTC; = 7am America/New_York — confirm DST offset at creation time, since routines have a 1-hour-minimum interval) |
| `enabled` | `true` |
| `mcp_connections[].name` | `"Airtable"` / `"Gmail"` (must match `[a-zA-Z0-9_-]`) |
| `mcp_connections[].url` | `"https://mcp.airtable.com/mcp"` / `"https://gmailmcp.googleapis.com/mcp/v1"` (fixed hosted MCP endpoints, same for every account) |
| `job_config.ccr.session_context.model` | `"claude-sonnet-5"` |
| `job_config.ccr.session_context.allowed_tools` | `["Bash", "Read", "Write", "Edit", "Glob", "Grep", "WebFetch", "WebSearch"]` — `WebFetch`/`WebSearch` are required: `run-events-daily/SKILL.md` fetches each source URL and, on the fallback path, web-searches for a replacement. Without them the routine can't do its core job. |
| `job_config.ccr.events` | One `user`-role event — `message.content` is the instruction text below, with the resolved recipient email embedded; give it a fresh lowercase v4 UUID and leave `session_id` empty |

After creation, save the returned routine ID / `https://claude.ai/code/routines/{id}` link for the final summary.

`RemoteTrigger` call shape, with the four resolved values as placeholders:

```json
{
  "name": "events-daily",
  "cron_expression": "0 11 * * *",
  "enabled": true,
  "mcp_connections": [
    {"connector_uuid": "<this account's Airtable connector UUID>", "name": "Airtable", "url": "https://mcp.airtable.com/mcp"},
    {"connector_uuid": "<this account's Gmail connector UUID>", "name": "Gmail", "url": "https://gmailmcp.googleapis.com/mcp/v1"}
  ],
  "job_config": {
    "ccr": {
      "environment_id": "<this account's full-network-access environment_id>",
      "session_context": {
        "model": "claude-sonnet-5",
        "sources": [{"git_repository": {"url": "<this checkout's origin URL, from `git remote get-url origin`>"}}],
        "allowed_tools": ["Bash", "Read", "Write", "Edit", "Glob", "Grep", "WebFetch", "WebSearch"]
      },
      "events": [
        {"data": {
          "uuid": "<generate a fresh lowercase v4 uuid>",
          "session_id": "",
          "type": "user",
          "parent_tool_use_id": null,
          "message": {
            "role": "user",
            "content": "Read the file .claude/skills/run-events-daily/SKILL.md in this repo and carry out the instructions in it exactly. The recipient email for the digest is <this account's DIGEST_RECIPIENT_EMAIL, from .env> — never send it anywhere else."
          }
        }}
      ]
    }
  }
}
```
