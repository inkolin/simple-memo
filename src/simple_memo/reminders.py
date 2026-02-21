"""Apple Reminders operations via AppleScript."""

from __future__ import annotations

from datetime import datetime

from . import colors
from .osascript import run, osa_escape


def list_reminders(show_completed: bool = False) -> list[dict]:
    """List reminders. By default only non-completed.

    Uses Unix timestamps for locale-independent date handling.
    AppleScript computes: (due_date - current date) + shell `date +%s`.
    """
    if show_completed:
        script = '''
            tell application "Reminders"
                set output to ""
                repeat with r in every reminder
                    set doneStr to "no"
                    if completed of r then set doneStr to "yes"
                    set ts to "none"
                    try
                        set dueDateR to due date of r
                        set ts to ((dueDateR - (current date)) + (do shell script "date +%s") as real) as string
                    end try
                    set output to output & id of r & "|" & name of r & "|" & ts & "|" & doneStr & linefeed
                end repeat
                return output
            end tell
        '''
    else:
        script = '''
            tell application "Reminders"
                set output to ""
                repeat with r in (reminders whose completed is false)
                    set ts to "none"
                    try
                        set dueDateR to due date of r
                        set ts to ((dueDateR - (current date)) + (do shell script "date +%s") as real) as string
                    end try
                    set output to output & id of r & "|" & name of r & "|" & ts & linefeed
                end repeat
                return output
            end tell
        '''

    raw = run(script)
    if raw.startswith("error:"):
        return []

    reminders = []
    for line in raw.strip().splitlines():
        parts = line.split("|")
        if len(parts) < 3:
            continue
        rid = parts[0].strip()
        title = parts[1].strip()
        ts_raw = parts[2].strip()
        completed = parts[3].strip() == "yes" if len(parts) > 3 else False

        due_date = None
        days_left = None
        due_display = "no due date"

        if ts_raw != "none":
            # Handle locale decimal: comma or dot
            ts_clean = ts_raw.replace(",", ".")
            try:
                due_date = datetime.fromtimestamp(float(ts_clean))
                due_display = due_date.strftime("%Y-%m-%d %H:%M")
                days_left = (due_date - datetime.now()).days
            except (ValueError, OSError):
                due_display = "invalid date"

        reminders.append({
            "id": rid,
            "title": title,
            "due_display": due_display,
            "due_date": due_date,
            "days_left": days_left,
            "completed": completed,
        })

    return reminders


def create_reminder(title: str, due_date: str | None = None, due_time: str = "09:00") -> bool:
    """Create a reminder. due_date format: YYYY-MM-DD, due_time: HH:MM."""
    esc_title = osa_escape(title)

    if due_date:
        try:
            dt = datetime.strptime(f"{due_date} {due_time}", "%Y-%m-%d %H:%M")
        except ValueError:
            print(colors.red("Invalid date format. Use YYYY-MM-DD HH:MM"))
            return False

        # Locale-independent: set date components individually.
        script = f'''
            tell application "Reminders"
                set dueDate to current date
                set year of dueDate to {dt.year}
                set month of dueDate to {dt.month}
                set day of dueDate to {dt.day}
                set time of dueDate to ({dt.hour} * hours + {dt.minute} * minutes)
                make new reminder with properties {{name:"{esc_title}", due date:dueDate}}
                return "created"
            end tell
        '''
    else:
        script = f'''
            tell application "Reminders"
                make new reminder with properties {{name:"{esc_title}"}}
                return "created"
            end tell
        '''

    result = run(script)
    if result.startswith("error:"):
        print(colors.red(f"Failed to create reminder: {result}"))
        return False
    print(colors.green(f"Created reminder: {title}"))
    return True


def complete_reminder(title: str) -> bool:
    """Mark a reminder as completed."""
    esc = osa_escape(title)
    script = f'''
        tell application "Reminders"
            set matchedReminders to (reminders whose name is "{esc}" and completed is false)
            if (count of matchedReminders) is 0 then
                return "error:not_found"
            end if
            set r to item 1 of matchedReminders
            set completed of r to true
            return "completed"
        end tell
    '''
    result = run(script)
    if result.startswith("error:"):
        print(colors.red(f"Reminder not found: {title}"))
        return False
    print(colors.green(f"Completed: {title}"))
    return True


def delete_reminder(title: str) -> bool:
    """Delete a reminder."""
    esc = osa_escape(title)
    script = f'''
        tell application "Reminders"
            set matchedReminders to (reminders whose name is "{esc}")
            if (count of matchedReminders) is 0 then
                return "error:not_found"
            end if
            delete item 1 of matchedReminders
            return "deleted"
        end tell
    '''
    result = run(script)
    if result.startswith("error:"):
        print(colors.red(f"Reminder not found: {title}"))
        return False
    print(colors.green(f"Deleted reminder: {title}"))
    return True


def edit_reminder(title: str, new_title: str | None = None, new_date: str | None = None) -> bool:
    """Edit a reminder's title or due date."""
    esc = osa_escape(title)

    if new_title:
        esc_new = osa_escape(new_title)
        script = f'''
            tell application "Reminders"
                set matchedReminders to (reminders whose name is "{esc}")
                if (count of matchedReminders) is 0 then
                    return "error:not_found"
                end if
                set r to item 1 of matchedReminders
                set name of r to "{esc_new}"
                return "updated"
            end tell
        '''
        result = run(script)
        if result.startswith("error:"):
            print(colors.red(f"Reminder not found: {title}"))
            return False
        print(colors.green(f"Renamed: {title} -> {new_title}"))
        return True

    if new_date:
        try:
            dt = datetime.strptime(new_date, "%Y-%m-%d %H:%M")
        except ValueError:
            print(colors.red("Invalid date format. Use: YYYY-MM-DD HH:MM"))
            return False

        script = f'''
            tell application "Reminders"
                set matchedReminders to (reminders whose name is "{esc}")
                if (count of matchedReminders) is 0 then
                    return "error:not_found"
                end if
                set r to item 1 of matchedReminders
                set dueDate to current date
                set year of dueDate to {dt.year}
                set month of dueDate to {dt.month}
                set day of dueDate to {dt.day}
                set time of dueDate to ({dt.hour} * hours + {dt.minute} * minutes)
                set due date of r to dueDate
                return "updated"
            end tell
        '''
        result = run(script)
        if result.startswith("error:"):
            print(colors.red(f"Reminder not found: {title}"))
            return False
        print(colors.green(f"Updated due date for: {title}"))
        return True

    print(colors.yellow("Nothing to update. Specify --new-title or --new-date."))
    return False


def print_reminders(rems: list[dict]) -> None:
    """Pretty-print reminders with color-coded urgency."""
    if not rems:
        print("No reminders found.")
        return

    for i, r in enumerate(rems, 1):
        title = r["title"]
        due = r["due_display"]
        days = r["days_left"]

        if days is not None:
            if days <= 1:
                line = colors.red(f"  {i}. {title}  |  {due}  |  {days}d left")
            elif days <= 3:
                line = colors.yellow(f"  {i}. {title}  |  {due}  |  {days}d left")
            else:
                line = f"  {colors.cyan(str(i))}. {title}  |  {colors.dim(due)}  |  {days}d left"
        else:
            line = f"  {colors.cyan(str(i))}. {title}  |  {colors.dim(due)}"

        print(line)
