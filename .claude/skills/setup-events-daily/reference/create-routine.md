# Create the daily routine

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
              "content": "Read the file .claude/skills/run-events-daily/SKILL.md in this repo and carry out the instructions in it exactly."
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
