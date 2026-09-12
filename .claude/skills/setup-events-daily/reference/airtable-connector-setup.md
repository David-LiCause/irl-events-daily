# Airtable connector setup

1. Go to claude.ai/customize/connectors → connect **Airtable** → select (or create) the base to scope it to.
2. Once connected, run `make setup-airtable` (creates the `events-daily` base with `Sources`/`EventLog` tables).

## Idempotency caveat
`scripts/setup_airtable.py` always creates a *new* base — it has no check for an existing `events-daily` base/tables. Before running it, check (via the Airtable connector) whether a base with those tables already exists, to avoid creating duplicates.
