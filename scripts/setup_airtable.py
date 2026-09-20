#!/usr/bin/env python3
"""Creates the Airtable base and Sources table via the Airtable Web API.

Usage: make setup-airtable  (reads AIRTABLE_PAT and AIRTABLE_WORKSPACE_ID from .env)
"""
import json
import os
import sys
import urllib.error
import urllib.request

API_ROOT = "https://api.airtable.com/v0/meta/bases"


def load_env(path=".env"):
    if not os.path.exists(path):
        return
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def api_request(method, url, token, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"API error {e.code}: {e.read().decode()}", file=sys.stderr)
        sys.exit(1)


def main():
    load_env()
    pat = os.environ.get("AIRTABLE_PAT")
    workspace_id = os.environ.get("AIRTABLE_WORKSPACE_ID")
    if not pat or not workspace_id:
        print(
            "Set AIRTABLE_PAT and AIRTABLE_WORKSPACE_ID in .env (see .env.example)",
            file=sys.stderr,
        )
        sys.exit(1)

    print("Creating base 'events-daily' with Sources table...")
    base = api_request(
        "POST",
        API_ROOT,
        pat,
        {
            "workspaceId": workspace_id,
            "name": "events-daily",
            "tables": [
                {
                    "name": "Sources",
                    "fields": [
                        {"name": "Name", "type": "singleLineText"},
                        {"name": "URL", "type": "url"},
                        {"name": "Instructions", "type": "multilineText"},
                    ],
                }
            ],
        },
    )
    base_id = base["id"]
    print(f"Base created: {base_id}")

    print(f"\nDone. Base ID: {base_id}")
    print("Select this base for the Airtable connector at claude.ai/customize/connectors.")


if __name__ == "__main__":
    main()
