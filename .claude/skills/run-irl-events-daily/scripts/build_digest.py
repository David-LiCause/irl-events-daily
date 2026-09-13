#!/usr/bin/env python3
"""Validates extracted events/sources and renders the daily digest email.

Usage: python3 build_digest.py events.json sources_report.json digest_output.json today

Reads a flat JSON array of events and a flat JSON array of source statuses
(see .claude/skills/run-irl-events-daily/SKILL.md step 5 for both schemas),
splits events into "today" (Date == today) and "this week" (later dates,
grouped by day), builds a Google Calendar "quick add" URL for each event,
and writes {"subject": ..., "body": ..., "htmlBody": ...} to the output path.
"""
import html
import itertools
import json
import sys
from datetime import datetime, timedelta
from urllib.parse import quote

FONT_STACK = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif"
COLOR_BG = "#f4f4f7"
COLOR_CARD = "#ffffff"
COLOR_BORDER = "#e5e7eb"
COLOR_TEXT = "#1f2937"
COLOR_MUTED = "#6b7280"
COLOR_ACCENT = "#2563eb"
COLOR_WARN_BG = "#fffbeb"
COLOR_WARN_BORDER = "#fde68a"
COLOR_WARN_TEXT = "#92400e"

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
    detail_parts = []
    if event.get("EventDescription"):
        detail_parts.append(event["EventDescription"])
    if event.get("SignupURL"):
        detail_parts.append(f"Sign up: {event['SignupURL']}")
    detail_parts.append(f"Source: {event['SourceURL']}")
    details = "\n\n".join(detail_parts)

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


def partition_events(events, today):
    """Splits events into today's list and (date, events) groups for the rest of the week."""
    today_events = sorted((e for e in events if e["Date"] == today), key=lambda e: e["StartDateTime"])
    upcoming = sorted((e for e in events if e["Date"] != today), key=lambda e: e["StartDateTime"])
    upcoming_groups = [(date, list(group)) for date, group in itertools.groupby(upcoming, key=lambda e: e["Date"])]
    return today_events, upcoming_groups


def format_date_header(date_str):
    return datetime.strptime(date_str, DATE_FMT).strftime("%A, %b %d")


def build_subject(today_count, upcoming_count):
    return f"[Claude Code Routine] Today's Events — {today_count} today, {upcoming_count} this week"


def render_event_block_text(event):
    lines = [event["EventTitle"], event["SourceName"], format_date_header(event["Date"])]
    if event.get("EventTime"):
        lines.append(event["EventTime"])
    lines.append(event["Location"])
    if event.get("Price"):
        lines.append(f"Price: {event['Price']}")
    if event.get("SignupURL"):
        lines.append(f"Sign up required: Yes ({event['SignupURL']})")
    else:
        lines.append("Sign up required: No")
    if event.get("EventDescription"):
        lines.append(event["EventDescription"])
    lines.append(f"Add to calendar: {build_quick_add_url(event)}")
    lines.append(f"Source: {event['SourceURL']}")
    return "\n".join(lines)


def render_email(events, sources, today):
    today_events, upcoming_groups = partition_events(events, today)
    upcoming_count = sum(len(group) for _, group in upcoming_groups)
    subject = build_subject(len(today_events), upcoming_count)

    today_body = (
        "\n\n---\n\n".join(render_event_block_text(e) for e in today_events)
        if today_events else "No events found for today."
    )
    sections = [f"TODAY\n\n{today_body}"]

    if upcoming_groups:
        day_blocks = []
        for date, group in upcoming_groups:
            day_body = "\n\n---\n\n".join(render_event_block_text(e) for e in group)
            day_blocks.append(f"{format_date_header(date)}\n\n{day_body}")
        upcoming_body = "\n\n---\n\n".join(day_blocks)
    else:
        upcoming_body = "No events found for the rest of the week."
    sections.append(f"COMING UP THIS WEEK\n\n{upcoming_body}")

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


def esc(value):
    return html.escape(str(value)) if value else ""


def render_event_card_html(event):
    detail_lines = [esc(format_date_header(event["Date"]))]
    if event.get("EventTime"):
        detail_lines.append(esc(event["EventTime"]))
    detail_lines.append(esc(event["Location"]))
    if event.get("Price"):
        detail_lines.append(f"Price: {esc(event['Price'])}")

    if event.get("SignupURL"):
        detail_lines.append("Sign up required: Yes")
    else:
        detail_lines.append("Sign up required: No")

    details_html = "<br>".join(detail_lines)

    description_html = ""
    if event.get("EventDescription"):
        description_html = (
            f'<div style="font-size:14px;color:{COLOR_TEXT};line-height:1.5;margin-bottom:16px;">'
            f'{esc(event["EventDescription"])}</div>'
        )

    buttons_html = ""
    if event.get("SignupURL"):
        buttons_html += (
            f'<a href="{esc(event["SignupURL"])}" style="display:inline-block;background-color:{COLOR_CARD};'
            f'color:{COLOR_ACCENT};text-decoration:none;padding:9px 18px;border-radius:6px;font-size:14px;'
            f'font-weight:600;border:1px solid {COLOR_ACCENT};margin-right:8px;">Sign Up</a>'
        )
    buttons_html += (
        f'<a href="{esc(build_quick_add_url(event))}" style="display:inline-block;background-color:{COLOR_ACCENT};'
        f'color:#ffffff;text-decoration:none;padding:10px 18px;border-radius:6px;font-size:14px;font-weight:600;">'
        f'Add to Calendar</a>'
    )

    return f'''
<div style="background-color:{COLOR_CARD};border:1px solid {COLOR_BORDER};border-radius:8px;padding:20px;margin-bottom:16px;">
  <div style="font-size:17px;font-weight:600;color:{COLOR_TEXT};margin-bottom:2px;">{esc(event["EventTitle"])}</div>
  <div style="font-size:13px;color:{COLOR_MUTED};margin-bottom:12px;">{esc(event["SourceName"])}</div>
  <div style="font-size:14px;color:{COLOR_MUTED};line-height:1.5;margin-bottom:12px;">{details_html}</div>
  {description_html}
  <div>{buttons_html}</div>
  <div style="font-size:13px;color:{COLOR_MUTED};margin-top:12px;"><a href="{esc(event["SourceURL"])}" style="color:{COLOR_ACCENT};">Source</a></div>
</div>'''


def render_empty_card_html(message):
    return (
        f'<div style="background-color:{COLOR_CARD};border:1px solid {COLOR_BORDER};'
        f'border-radius:8px;padding:20px;color:{COLOR_MUTED};font-size:14px;">'
        f"{esc(message)}</div>"
    )


def render_section_header_html(label, large=False):
    font_size = "20px" if large else "15px"
    return f'<div style="font-size:{font_size};font-weight:700;color:{COLOR_TEXT};margin:0 0 12px 0;">{esc(label)}</div>'


def render_date_subheader_html(date_str):
    return (
        f'<div style="font-size:16px;font-weight:600;color:{COLOR_MUTED};margin:16px 0 8px 0;'
        f'padding-top:8px;border-top:1px solid {COLOR_BORDER};">{esc(format_date_header(date_str))}</div>'
    )


def render_email_html(events, sources, today):
    today_events, upcoming_groups = partition_events(events, today)
    upcoming_count = sum(len(group) for _, group in upcoming_groups)
    subject = build_subject(len(today_events), upcoming_count)

    today_html = (
        "\n".join(render_event_card_html(e) for e in today_events)
        if today_events else render_empty_card_html("No events found for today.")
    )

    if upcoming_groups:
        upcoming_html = "\n".join(
            render_date_subheader_html(date) + "\n" + "\n".join(render_event_card_html(e) for e in group)
            for date, group in upcoming_groups
        )
    else:
        upcoming_html = render_empty_card_html("No events found for the rest of the week.")

    events_html = f'''
{today_html}
<div style="margin-top:24px;">
{render_section_header_html("Coming up this week", large=True)}
{upcoming_html}
</div>'''

    blocked = [s for s in sources if s["Status"] == "blocked"]
    blocked_html = ""
    if blocked:
        items = "\n".join(
            f'<li style="margin-bottom:4px;"><a href="{esc(s["URL"])}" style="color:{COLOR_WARN_TEXT};">{esc(s["Name"])}</a> — {esc(s["Reason"])}</li>'
            for s in blocked
        )
        blocked_html = f'''
<div style="background-color:{COLOR_WARN_BG};border:1px solid {COLOR_WARN_BORDER};border-radius:8px;padding:16px 16px 16px 20px;margin-bottom:16px;">
  <div style="font-size:14px;font-weight:600;color:{COLOR_WARN_TEXT};margin-bottom:8px;">Could not check automatically — please visit these manually:</div>
  <ul style="margin:0;padding-left:16px;color:{COLOR_WARN_TEXT};font-size:13px;">{items}</ul>
</div>'''

    summary_items = "<br>".join(
        f'{"OK" if s["Status"] == "ok" else "BLOCKED"} — {esc(s["Name"])}: <a href="{esc(s["URL"])}" style="color:{COLOR_MUTED};">{esc(s["URL"])}</a>'
        for s in sources
    )
    summary_html = f'''
<div style="font-size:12px;color:{COLOR_MUTED};padding-top:16px;border-top:1px solid {COLOR_BORDER};line-height:1.6;">
  <div style="margin-bottom:6px;">Sources checked today ({len(sources)}):</div>
  {summary_items}
</div>'''

    return f'''<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(subject)}</title>
</head>
<body style="margin:0;padding:0;background-color:{COLOR_BG};font-family:{FONT_STACK};">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:{COLOR_BG};padding:24px 0;">
<tr><td align="center">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background-color:{COLOR_CARD};border-radius:8px;">
<tr><td style="padding:24px 24px 8px 24px;">
  <div style="font-size:20px;font-weight:700;color:{COLOR_TEXT};">Today's Events</div>
  <div style="font-size:14px;color:{COLOR_MUTED};margin-top:4px;">{esc(today)} &mdash; {len(today_events)} today &middot; {upcoming_count} this week</div>
</td></tr>
<tr><td style="padding:16px 24px 24px 24px;">
{events_html}
{blocked_html}
{summary_html}
</td></tr>
</table>
</td></tr>
</table>
</body>
</html>'''


def main():
    if len(sys.argv) != 5:
        print("Usage: python3 build_digest.py events.json sources_report.json digest_output.json today", file=sys.stderr)
        sys.exit(1)

    events_path, sources_path, output_path, today = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    try:
        datetime.strptime(today, DATE_FMT)
    except ValueError:
        print(f"'today' is not a valid 'YYYY-MM-DD' date: {today!r}", file=sys.stderr)
        sys.exit(1)

    with open(events_path) as f:
        events = json.load(f)
    with open(sources_path) as f:
        sources = json.load(f)

    validate(events)
    validate_sources(sources)
    subject, body = render_email(events, sources, today)
    html_body = render_email_html(events, sources, today)

    with open(output_path, "w") as f:
        json.dump({"subject": subject, "body": body, "htmlBody": html_body}, f, indent=2)

    print(f"Wrote digest for {len(events)} event(s), {len(sources)} source(s) to {output_path}")


if __name__ == "__main__":
    main()
