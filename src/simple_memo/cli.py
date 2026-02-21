"""CLI entry point for simple-memo using Click."""

import sys

import click

from . import __version__, colors
from .osascript import require_macos
from . import notes, reminders


@click.group(invoke_without_command=True)
@click.version_option(__version__, prog_name="simple-memo")
@click.pass_context
def main(ctx):
    """simple-memo — A simple CLI for Apple Notes & Reminders on macOS."""
    require_macos()
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


# ─── Notes commands ───────────────────────────────────────────────────────────


@main.command("list")
@click.option("-f", "--folder", default=None, help="Filter notes by folder name.")
def cmd_list(folder):
    """List all notes (optionally filtered by folder)."""
    result = notes.list_notes(folder)
    notes._print_notes_list(result)


@main.command("folders")
def cmd_folders():
    """List all folders in Apple Notes."""
    folders = notes.list_folders()
    if not folders:
        print("No folders found.")
        return
    for f in folders:
        print(f"  {f}")


@main.command("read")
@click.argument("title")
def cmd_read(title):
    """Read a note by title."""
    content = notes.read_note(title)
    if content is None:
        print(colors.red(f"Note not found: {title}"))
        sys.exit(1)
    print(f"\n{colors.bold(title)}\n")
    print(content)


@main.command("create")
@click.argument("title", required=False)
@click.argument("body", required=False)
@click.option("-f", "--folder", default="Notes", help="Folder to create note in.")
@click.option("-i", "--interactive", is_flag=True, help="Open $EDITOR to write the note.")
def cmd_create(title, body, folder, interactive):
    """Create a new note. Use -i to open in $EDITOR."""
    if interactive or title is None:
        notes.create_note_interactive(folder)
        return

    # Read from stdin if no body and stdin is piped
    if body is None and not sys.stdin.isatty():
        body = sys.stdin.read().strip()

    if notes.create_note(title, body or "", folder):
        print(colors.green(f"Created: {title}"))
    else:
        print(colors.red("Failed to create note."))
        sys.exit(1)


@main.command("edit")
@click.argument("title")
def cmd_edit(title):
    """Edit a note in $EDITOR (Markdown)."""
    if not notes.edit_note(title):
        sys.exit(1)


@main.command("append")
@click.argument("title")
@click.argument("text")
def cmd_append(title, text):
    """Append text to an existing note."""
    if not notes.append_note(title, text):
        sys.exit(1)


@main.command("delete")
@click.argument("title")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation.")
def cmd_delete(title, yes):
    """Delete a note by title."""
    if not yes:
        click.confirm(f"Delete note '{title}'?", abort=True)
    if not notes.delete_note(title):
        sys.exit(1)


@main.command("move")
@click.argument("title")
@click.argument("target_folder")
def cmd_move(title, target_folder):
    """Move a note to a different folder."""
    if not notes.move_note(title, target_folder):
        sys.exit(1)


@main.command("search")
@click.argument("query", required=False)
@click.option("--fzf", "use_fzf", is_flag=True, help="Use interactive fzf search.")
def cmd_search(query, use_fzf):
    """Search notes by content or title. Use --fzf for interactive mode."""
    if use_fzf or query is None:
        notes.fuzzy_search()
        return

    results = notes.search_notes(query)
    notes._print_notes_list(results)


@main.command("count")
def cmd_count():
    """Count total notes."""
    n = notes.count_notes()
    print(f"Total notes: {n}")


@main.command("export")
@click.option("-o", "--output", default=None, help="Output directory (default: ~/Desktop/simple-memo-export).")
@click.option("--html", "as_html", is_flag=True, help="Export as HTML instead of Markdown.")
def cmd_export(output, as_html):
    """Export all notes to files (Markdown or HTML)."""
    count = notes.export_notes(output, as_markdown=not as_html)
    print(colors.green(f"Exported {count} notes."))


@main.command("mkfolder")
@click.argument("name")
def cmd_mkfolder(name):
    """Create a new folder in Apple Notes."""
    notes.create_folder(name)


@main.command("rmfolder")
@click.argument("name")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation.")
def cmd_rmfolder(name, yes):
    """Delete a folder from Apple Notes."""
    if not yes:
        click.confirm(
            f"Delete folder '{name}'? All notes inside will be deleted!",
            abort=True,
        )
    notes.delete_folder(name)


# ─── Reminders commands ──────────────────────────────────────────────────────


@main.group("rem")
def cmd_rem():
    """Manage Apple Reminders."""
    pass


@cmd_rem.command("list")
@click.option("-a", "--all", "show_all", is_flag=True, help="Include completed reminders.")
def rem_list(show_all):
    """List reminders (non-completed by default)."""
    result = reminders.list_reminders(show_completed=show_all)
    reminders.print_reminders(result)


@cmd_rem.command("add")
@click.argument("title")
@click.option("-d", "--date", "due_date", default=None, help="Due date: YYYY-MM-DD")
@click.option("-t", "--time", "due_time", default="09:00", help="Due time: HH:MM (default: 09:00)")
def rem_add(title, due_date, due_time):
    """Create a new reminder."""
    reminders.create_reminder(title, due_date, due_time)


@cmd_rem.command("done")
@click.argument("title")
def rem_done(title):
    """Mark a reminder as completed."""
    if not reminders.complete_reminder(title):
        sys.exit(1)


@cmd_rem.command("delete")
@click.argument("title")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation.")
def rem_delete(title, yes):
    """Delete a reminder."""
    if not yes:
        click.confirm(f"Delete reminder '{title}'?", abort=True)
    if not reminders.delete_reminder(title):
        sys.exit(1)


@cmd_rem.command("edit")
@click.argument("title")
@click.option("--new-title", default=None, help="New title for the reminder.")
@click.option("--new-date", default=None, help="New due date: YYYY-MM-DD HH:MM")
def rem_edit(title, new_title, new_date):
    """Edit a reminder (title or due date)."""
    if not reminders.edit_reminder(title, new_title, new_date):
        sys.exit(1)
