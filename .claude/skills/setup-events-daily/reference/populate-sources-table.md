# Populate the Sources table

1. Ask the user for their list of orgs/venues to track, each with one or more event-page URLs.
2. Confirm the parsed list back to the user (org name → URL(s)) before writing anything.
3. Write one row per org/URL pair via the Airtable connector (`Name`, `URL` columns).
4. Read the table back and show the user the final row count/contents to verify.
