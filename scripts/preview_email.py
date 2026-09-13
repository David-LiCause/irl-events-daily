#!/usr/bin/env python3
"""Renders the daily digest email against hardcoded sample data, so you can
see and iterate on what the email looks like without running the full skill
or touching Airtable/Gmail.

Usage: python3 scripts/preview_email.py  (or `make preview-email`)
Writes one .txt file per scenario to dev/email_previews/.
"""
import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BUILD_DIGEST_PATH = REPO_ROOT / ".claude/skills/run-events-daily/scripts/build_digest.py"
OUTPUT_DIR = REPO_ROOT / "dev" / "email_previews"

spec = importlib.util.spec_from_file_location("build_digest", BUILD_DIGEST_PATH)
build_digest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_digest)


def scenario_typical_day():
    """A normal day: a mix of timed/all-day events, with/without price or signup link, plus one flagged source."""
    events = [
        {
            "Date": "2026-09-12", "DigestIndex": None,
            "EventTitle": "Trivia Night", "EventDescription": "Weekly bar trivia, teams of up to 6.",
            "EventTime": "7:00 PM - 9:00 PM", "StartDateTime": "2026-09-12T19:00:00",
            "EndDateTime": "2026-09-12T21:00:00", "AllDay": False,
            "Location": "The Pub, 123 Main St", "Price": "Free", "SignupURL": None,
            "SourceName": "The Pub", "SourceURL": "https://thepub.example.com/events",
            "Sent": False, "AddedToCalendar": False, "CalendarEventId": None,
        },
        {
            "Date": "2026-09-12", "DigestIndex": None,
            "EventTitle": "Live Jazz: The Blue Notes", "EventDescription": "",
            "EventTime": "8:30 PM", "StartDateTime": "2026-09-12T20:30:00",
            "EndDateTime": None, "AllDay": False,
            "Location": "Riverside Jazz Club", "Price": "$15 cover",
            "SignupURL": "https://riverside.example.com/tickets",
            "SourceName": "Riverside Jazz Club", "SourceURL": "https://riverside.example.com/calendar",
            "Sent": False, "AddedToCalendar": False, "CalendarEventId": None,
        },
        {
            "Date": "2026-09-12", "DigestIndex": None,
            "EventTitle": "Community Farmers Market",
            "EventDescription": "Local produce, crafts, and live music all day.",
            "EventTime": "", "StartDateTime": "2026-09-12T00:00:00",
            "EndDateTime": None, "AllDay": True,
            "Location": "Town Square", "Price": None, "SignupURL": None,
            "SourceName": "Town Square Events", "SourceURL": "https://townsquare.example.com/events",
            "Sent": False, "AddedToCalendar": False, "CalendarEventId": None,
        },
    ]
    sources = [
        {"Name": "The Pub", "URL": "https://thepub.example.com/events", "Status": "ok"},
        {"Name": "Riverside Jazz Club", "URL": "https://riverside.example.com/calendar", "Status": "ok"},
        {"Name": "Town Square Events", "URL": "https://townsquare.example.com/events", "Status": "ok"},
        {"Name": "Downtown Theater", "URL": "https://downtowntheater.example.com", "Status": "blocked", "Reason": "403 Forbidden"},
    ]
    return events, sources


def scenario_no_events_found():
    """Every source checked fine, but nothing is happening today."""
    events = []
    sources = [
        {"Name": "The Pub", "URL": "https://thepub.example.com/events", "Status": "ok"},
        {"Name": "Riverside Jazz Club", "URL": "https://riverside.example.com/calendar", "Status": "ok"},
    ]
    return events, sources


def scenario_multiple_sources_blocked():
    """A rougher day: some events found, but several sources couldn't be checked at all."""
    events = [
        {
            "Date": "2026-09-12", "DigestIndex": None,
            "EventTitle": "Open Mic Night", "EventDescription": "Sign up at the door.",
            "EventTime": "8:00 PM", "StartDateTime": "2026-09-12T20:00:00",
            "EndDateTime": None, "AllDay": False,
            "Location": "The Pub", "Price": "Free", "SignupURL": None,
            "SourceName": "The Pub", "SourceURL": "https://thepub.example.com/events",
            "Sent": False, "AddedToCalendar": False, "CalendarEventId": None,
        },
    ]
    sources = [
        {"Name": "The Pub", "URL": "https://thepub.example.com/events", "Status": "ok"},
        {"Name": "Downtown Theater", "URL": "https://downtowntheater.example.com", "Status": "blocked", "Reason": "403 Forbidden"},
        {"Name": "Civic Center", "URL": "https://civiccenter.example.com/calendar", "Status": "blocked", "Reason": "no parseable events list found"},
    ]
    return events, sources


SCENARIOS = {
    "typical_day": scenario_typical_day,
    "no_events_found": scenario_no_events_found,
    "multiple_sources_blocked": scenario_multiple_sources_blocked,
}


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, build_scenario in SCENARIOS.items():
        events, sources = build_scenario()
        build_digest.validate(events)
        build_digest.validate_sources(sources)
        subject, body = build_digest.render_email(events, sources)

        out_path = OUTPUT_DIR / f"{name}.txt"
        out_path.write_text(f"Subject: {subject}\n\n{body}\n")
        print(f"Wrote {out_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
