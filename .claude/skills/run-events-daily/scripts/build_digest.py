#!/usr/bin/env python3
"""Validates extracted events/sources and renders the daily digest email.

Usage: python3 build_digest.py events.json sources_report.json digest_output.json

Reads a flat JSON array of events and a flat JSON array of source statuses
(see .claude/skills/run-events-daily/SKILL.md step 5 for both schemas),
builds a Google Calendar "quick add" URL for each event, and writes
{"subject": ..., "body": ...} to the output path.
"""
import json
import sys
from datetime import datetime, timedelta
from urllib.parse import quote

REQUIRED_FIELDS = ["EventTitle", "Location", "SourceName", "SourceURL", "StartDateTime", "AllDay"]
SOURCE_STATUSES = ("ok", "blocked")

DATETIME_FMT = "%Y-%m-%dT%H:%M:%S"
DATE_FMT = "%Y-%m-%d"


def fail(index, title, message):
    label = title or f"event at index {index}"
    print(f"Invalid event ({label}): {message}", file=sys.stderr)
    sys.exit(1)


def parse_datetime(value, index, title, field):
    try:
        return datetime.strptime(value, DATETIME_FMT)
    except ValueError:
        fail(index, title, f"{field} is not a valid 'YYYY-MM-DDTHH:MM:SS' datetime: {value!r}")


def parse_date(value, index, title, field):
    try:
        return datetime.strptime(value, DATE_FMT)
    except ValueError:
        fail(index, title, f"{field} is not a valid 'YYYY-MM-DD' date: {value!r}")


def validate(events):
    for i, event in enumerate(events):
        title = event.get("EventTitle")
        for field in REQUIRED_FIELDS:
            if event.get(field) in (None, ""):
                fail(i, title, f"missing required field '{field}'")

        if not isinstance(event["AllDay"], bool):
            fail(i, title, f"'AllDay' must be a boolean, got {event['AllDay']!r}")

        if event.get("Date"):
            parse_date(event["Date"], i, title, "Date")

        if event["AllDay"]:
            parse_date(event["StartDateTime"][:10], i, title, "StartDateTime")
            if event.get("EndDateTime"):
                parse_date(event["EndDateTime"][:10], i, title, "EndDateTime")
        else:
            parse_datetime(event["StartDateTime"], i, title, "StartDateTime")
            if event.get("EndDateTime"):
                parse_datetime(event["EndDateTime"], i, title, "EndDateTime")


def validate_sources(sources):
    for i, source in enumerate(sources):
        name = source.get("Name")
        label = name or f"source at index {i}"
        for field in ("Name", "URL", "Status"):
            if source.get(field) in (None, ""):
                print(f"Invalid source ({label}): missing required field '{field}'", file=sys.stderr)
                sys.exit(1)
        if source["Status"] not in SOURCE_STATUSES:
            print(f"Invalid source ({label}): 'Status' must be one of {SOURCE_STATUSES}, got {source['Status']!r}", file=sys.stderr)
            sys.exit(1)
        if source["Status"] == "blocked" and not source.get("Reason"):
            print(f"Invalid source ({label}): 'blocked' sources require a 'Reason'", file=sys.stderr)
            sys.exit(1)


def build_quick_add_url(event):
    details = event.get("EventDescription") or ""
    link = event.get("SignupURL") or event.get("SourceURL")
    if link:
        details = f"{details}\n\n{link}" if details else link

    if event["AllDay"]:
        start = datetime.strptime(event["StartDateTime"][:10], DATE_FMT)
        if event.get("EndDateTime"):
            end = datetime.strptime(event["EndDateTime"][:10], DATE_FMT)
        else:
            end = start + timedelta(days=1)
        dates = f"{start.strftime('%Y%m%d')}/{end.strftime('%Y%m%d')}"
    else:
        start = datetime.strptime(event["StartDateTime"], DATETIME_FMT)
        if event.get("EndDateTime"):
            end = datetime.strptime(event["EndDateTime"], DATETIME_FMT)
        else:
            end = start + timedelta(hours=2)
        dates = f"{start.strftime('%Y%m%dT%H%M%S')}/{end.strftime('%Y%m%dT%H%M%S')}"

    params = (
        f"action=TEMPLATE"
        f"&text={quote(event['EventTitle'])}"
        f"&dates={dates}"
        f"&details={quote(details)}"
        f"&location={quote(event['Location'])}"
        f"&ctz=America/New_York"
    )
    return f"https://www.google.com/calendar/render?{params}"


def render_email(events, sources):
    date = events[0].get("Date", "") if events else ""
    subject = f"Events Daily: {date} — {len(events)} event(s) found"

    blocks = []
    for event in events:
        lines = [event["EventTitle"]]
        if event.get("EventTime"):
            lines.append(event["EventTime"])
        lines.append(event["Location"])
        if event.get("Price"):
            lines.append(f"Price: {event['Price']}")
        lines.append(f"Add to calendar: {build_quick_add_url(event)}")
        if event.get("SignupURL"):
            lines.append(f"Signup: {event['SignupURL']}")
        lines.append(f"Source: {event['SourceURL']}")
        blocks.append("\n".join(lines))

    sections = ["\n\n---\n\n".join(blocks) if blocks else "No events found for today."]

    blocked = [s for s in sources if s["Status"] == "blocked"]
    if blocked:
        lines = ["Could not check automatically — please visit these manually:"]
        for s in blocked:
            lines.append(f"- {s['Name']}: {s['URL']} ({s['Reason']})")
        sections.append("\n".join(lines))

    summary_lines = [f"Sources checked today ({len(sources)}):"]
    for s in sources:
        mark = "OK" if s["Status"] == "ok" else "BLOCKED"
        summary_lines.append(f"[{mark}] {s['Name']}: {s['URL']}")
    sections.append("\n".join(summary_lines))

    body = "\n\n===\n\n".join(sections)
    return subject, body


def main():
    if len(sys.argv) != 4:
        print("Usage: python3 build_digest.py events.json sources_report.json digest_output.json", file=sys.stderr)
        sys.exit(1)

    events_path, sources_path, output_path = sys.argv[1], sys.argv[2], sys.argv[3]

    with open(events_path) as f:
        events = json.load(f)
    with open(sources_path) as f:
        sources = json.load(f)

    validate(events)
    validate_sources(sources)
    subject, body = render_email(events, sources)

    with open(output_path, "w") as f:
        json.dump({"subject": subject, "body": body}, f, indent=2)

    print(f"Wrote digest for {len(events)} event(s), {len(sources)} source(s) to {output_path}")


if __name__ == "__main__":
    main()
