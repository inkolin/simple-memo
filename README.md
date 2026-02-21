# simple-memo

A simple, MIT-licensed CLI for Apple Notes & Reminders on macOS.

Use it from the terminal, scripts, or AI agents — no restrictions, no confirmation dialogs.

## Features

- Full Apple Notes management (create, read, edit, append, move, delete, search, export)
- Full Apple Reminders management (add, complete, edit, delete)
- No confirmation dialogs — all operations resolve internally via Apple's note/reminder IDs
- AI-agent friendly — every command works non-interactively with `-y` flag
- Markdown in, Markdown out — notes are stored as HTML but you work in Markdown
- Interactive fuzzy search with [fzf](https://github.com/junegunn/fzf) support
- Pipe-friendly — create notes from stdin

## Install

```bash
pip install simple-memo
# or
pipx install simple-memo
```

## Notes

```bash
simple-memo list                          # List all notes
simple-memo list -f Work                  # List notes in a folder
simple-memo folders                       # List all folders
simple-memo read "Meeting Notes"          # Read a note (Markdown)
simple-memo create "Title" "Body text"    # Create a note
simple-memo create -i                     # Create in $EDITOR
simple-memo create "Title" -f Work        # Create in specific folder
echo "piped" | simple-memo create "Title" # Create from stdin
simple-memo edit "Meeting Notes"          # Edit in $EDITOR
simple-memo append "Title" "More text"    # Append to a note
simple-memo move "Title" "Archive"        # Move to folder (creates if needed)
simple-memo search "keyword"              # Search by content/title
simple-memo search --fzf                  # Interactive fuzzy search (requires fzf)
simple-memo delete -y "Old Note"          # Delete a note
simple-memo count                         # Count total notes
simple-memo export                        # Export all to ~/Desktop/simple-memo-export/
simple-memo export -o ./backup            # Export to custom directory
simple-memo export --html                 # Export as HTML instead of Markdown
simple-memo mkfolder "Projects"           # Create a folder
simple-memo rmfolder -y "Old Stuff"       # Delete a folder
```

## Reminders

```bash
simple-memo rem list                      # List non-completed reminders
simple-memo rem list -a                   # List all (including completed)
simple-memo rem add "Buy milk"            # Create reminder (no due date)
simple-memo rem add "Meeting" -d 2025-03-01 -t 14:00  # With due date
simple-memo rem done "Buy milk"           # Mark as completed
simple-memo rem edit "Meeting" --new-title "Team sync"  # Rename
simple-memo rem edit "Meeting" --new-date "2025-03-05 10:00"  # Reschedule
simple-memo rem delete -y "Old reminder"  # Delete
```

## No Confirmation Dialogs

Other Apple Notes CLI tools get stuck on macOS confirmation dialogs when deleting notes or reminders. `simple-memo` resolves every operation via Apple's internal note/reminder IDs, which bypasses all system dialogs completely. Delete, move, edit — everything works instantly without any popups or timeouts.

## Why?

Existing Apple Notes CLI tools use restrictive licenses that prohibit AI usage. `simple-memo` is MIT-licensed — use it however you want, including with AI agents, commercial products, and automation scripts.

## Requirements

- macOS (uses AppleScript to talk to Apple Notes & Reminders)
- Python 3.9+
- Optional: [fzf](https://github.com/junegunn/fzf) for interactive search

## License

MIT — see [LICENSE](LICENSE)
