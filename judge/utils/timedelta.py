import datetime

from django.utils.translation import ngettext, npgettext, pgettext


def _format_simple_no_seconds(days, hours, minutes):
    """Format timedelta in simple-no-seconds style."""
    if days:
        if hours or minutes:
            return f"{days} day{'' if days == 1 else 's'} {hours}:{minutes:02d}"
        return f"{days} day{'' if days == 1 else 's'}"
    return f"{hours}:{minutes:02d}"


def _format_sql(days, hours, minutes, seconds):
    """Format timedelta in SQL style."""
    return f"{days} {hours:02d}:{minutes:02d}:{seconds:02d}"


def _format_simple(days, hours, minutes, seconds):
    """Format timedelta in simple style."""
    if days:
        return f"{days} day{'' if days == 1 else 's'} {hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _format_localized(days, hours, minutes, seconds):
    """Format timedelta in localized style."""
    if days:
        return (
            npgettext("time format with day", "%d day %h:%m:%s", "%d days %h:%m:%s", days)
            .replace("%d", str(days))
            .replace("%h", f"{hours:02d}")
            .replace("%m", f"{minutes:02d}")
            .replace("%s", f"{seconds:02d}")
        )
    return (
        pgettext("time format without day", "%h:%m:%s")
        .replace("%h", f"{hours:02d}")
        .replace("%m", f"{minutes:02d}")
        .replace("%s", f"{seconds:02d}")
    )


def _format_localized_no_seconds(days, hours, minutes):
    """Format timedelta in localized-no-seconds style."""
    if days:
        if hours or minutes:
            return (
                npgettext("time format no seconds with day", "%d day %h:%m", "%d days %h:%m", days)
                .replace("%d", str(days))
                .replace("%h", f"{hours:02d}")
                .replace("%m", f"{minutes:02d}")
            )
        return ngettext("%d day", "%d days", days) % days
    return pgettext("hours and minutes", "%h:%m").replace("%h", f"{hours:02d}").replace("%m", f"{minutes:02d}")


def _format_concise(days, hours, minutes, seconds):
    """Format timedelta in concise style."""
    if days:
        return f"{days}d {hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _format_noday(days, hours, minutes, seconds):
    """Format timedelta in noday style."""
    hours += days * 24
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _format_standard(weeks, days, hours, minutes, seconds, display, sep):
    """Format timedelta in standard word-based styles (minimal, short, long)."""
    if display == "minimal":
        words = ["w", "d", "h", "m", "s"]
    elif display == "short":
        words = [" wks", " days", " hrs", " min", " sec"]
    else:
        words = [" weeks", " days", " hours", " minutes", " seconds"]

    values = [weeks, days, hours, minutes, seconds]
    result = []

    for i in range(len(values)):
        if values[i]:
            if values[i] == 1 and len(words[i]) > 1:
                result.append(f"{values[i]}{words[i].rstrip('s')}")
            else:
                result.append(f"{values[i]}{words[i]}")

    return sep.join(result)


def nice_repr(timedelta, display="long", sep=", "):
    """
    Turns a datetime.timedelta object into a nice string repr.

    display can be 'minimal', 'short' or 'long' [default].

    >>> from datetime import timedelta as td
    >>> nice_repr(td(days=1, hours=2, minutes=3, seconds=4))
    '1 day, 2 hours, 3 minutes, 4 seconds'
    >>> nice_repr(td(days=1, seconds=1), 'minimal')
    '1d, 1s'
    """
    assert isinstance(timedelta, datetime.timedelta), "First argument must be a timedelta."

    weeks = timedelta.days // 7
    days = timedelta.days % 7
    hours = timedelta.seconds // 3600
    minutes = (timedelta.seconds % 3600) // 60
    seconds = timedelta.seconds % 60

    # For most formats, combine weeks and days
    total_days = days + weeks * 7

    format_handlers = {
        "simple-no-seconds": lambda: _format_simple_no_seconds(total_days, hours, minutes),
        "sql": lambda: _format_sql(total_days, hours, minutes, seconds),
        "simple": lambda: _format_simple(total_days, hours, minutes, seconds),
        "localized": lambda: _format_localized(total_days, hours, minutes, seconds),
        "localized-no-seconds": lambda: _format_localized_no_seconds(total_days, hours, minutes),
        "concise": lambda: _format_concise(total_days, hours, minutes, seconds),
        "noday": lambda: _format_noday(total_days, hours, minutes, seconds),
    }

    if display in format_handlers:
        return format_handlers[display]()

    # Default to standard word-based formatting for minimal, short, long
    return _format_standard(weeks, days, hours, minutes, seconds, display, sep)
