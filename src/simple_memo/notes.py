"""Apple Notes operations via AppleScript."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from . import convert, colors
from .osascript import run, osa_escape

# "Recently Deleted" folder names in 28+ languages — filter these out.
TRASH_NAMES = {
    "recently deleted", "zuletzt gelöscht", "supprimés récemment",
    "eliminados recientemente", "eliminati di recente", "最近削除した項目",
    "最近删除", "최근 삭제한 항목", "recentemente apagadas",
    "недавно удалённые", "onlangs verwijderd", "senast raderade",
    "son silinenler", "ostatnio usunięte", "nedávno smazané",
    "nemrég törölt", "recent șterse", "nylig slettet",
    "nylig slettet", "äskettäin poistetut", "πρόσφατα διαγραμμένα",
    "נמחקו לאחרונה", "المحذوفة مؤخرًا", "เพิ่งลบล่าสุด",
    "gần đây đã xóa", "recently deleted",
}


def list_notes(folder: str | None = None) -> list[dict]:
    """Return a list of notes as [{id, title, folder}]."""
    if folder:
        esc = osa_escape(folder)
        script = f'''
            tell application "Notes"
                set f to folder "{esc}"
                set output to ""
                repeat with n in notes of f
                    set output to output & id of n & "|" & name of n & "|" & name of container of n & linefeed
                end repeat
                return output
            end tell
        '''
    else:
        script = '''
            tell application "Notes"
                set output to ""
                repeat with n in every note
                    set output to output & id of n & "|" & name of n & "|" & name of container of n & linefeed
                end repeat
                return output
            end tell
        '''

    raw = run(script)
    if raw.startswith("error:"):
        return []

    notes = []
    seen_ids = set()
    for line in raw.strip().splitlines():
        parts = line.split("|", 2)
        if len(parts) < 3:
            continue
        nid, title, fld = parts[0].strip(), parts[1].strip(), parts[2].strip()
        if fld.lower() in TRASH_NAMES:
            continue
        if nid in seen_ids:
            continue
        seen_ids.add(nid)
        notes.append({"id": nid, "title": title, "folder": fld})

    return notes


def list_folders() -> list[str]:
    """Return a list of folder names."""
    script = '''
        tell application "Notes"
            set output to ""
            repeat with f in every folder
                set output to output & name of f & linefeed
            end repeat
            return output
        end tell
    '''
    raw = run(script)
    if raw.startswith("error:"):
        return []

    folders = []
    for line in raw.strip().splitlines():
        name = line.strip()
        if name and name.lower() not in TRASH_NAMES:
            folders.append(name)
    return folders


def read_note(title: str) -> str | None:
    """Read a note's content as Markdown (converted from HTML)."""
    note_id = _resolve_id(title)
    if note_id is None:
        return None
    return read_note_by_id(note_id)


def read_note_by_id(note_id: str) -> str | None:
    """Read a note's content as Markdown by ID."""
    esc = osa_escape(note_id)
    script = f'''
        tell application "Notes"
            set theNote to first note whose id is "{esc}"
            return body of theNote
        end tell
    '''
    raw = run(script)
    if raw.startswith("error:"):
        return None
    return convert.html_to_md(raw)


def read_note_html(title: str) -> str | None:
    """Read a note's raw HTML body."""
    note_id = _resolve_id(title)
    if note_id is None:
        return None
    return read_note_html_by_id(note_id)


def read_note_html_by_id(note_id: str) -> str | None:
    """Read a note's raw HTML body by ID."""
    esc = osa_escape(note_id)
    script = f'''
        tell application "Notes"
            set theNote to first note whose id is "{esc}"
            return body of theNote
        end tell
    '''
    raw = run(script)
    if raw.startswith("error:"):
        return None
    return raw


def create_note(title: str, body: str = "", folder: str = "Notes") -> bool:
    """Create a new note. Body is Markdown, converted to HTML for storage."""
    esc_title = osa_escape(title)
    html_body = convert.md_to_html(body) if body else ""
    esc_body = osa_escape(f"<h1>{title}</h1>{html_body}")
    esc_folder = osa_escape(folder)

    script = f'''
        tell application "Notes"
            tell folder "{esc_folder}"
                make new note with properties {{name:"{esc_title}", body:"{esc_body}"}}
            end tell
        end tell
    '''
    result = run(script)
    return not result.startswith("error:")


def create_note_interactive(folder: str = "Notes") -> bool:
    """Open $EDITOR for the user to write a note in Markdown."""
    editor = os.environ.get("EDITOR", "vim")
    template = "# Note Title\n\nWrite your note here in Markdown.\n"

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", prefix="simple-memo-", delete=False
    ) as f:
        f.write(template)
        tmp_path = f.name

    try:
        subprocess.run([editor, tmp_path], check=True)
        content = Path(tmp_path).read_text().strip()

        if content == template.strip():
            print(colors.yellow("No changes — note creation cancelled."))
            return False

        lines = content.splitlines()
        title = lines[0].lstrip("# ").strip() if lines else "Untitled"
        body = "\n".join(lines[1:]).strip()

        if create_note(title, body, folder):
            print(colors.green(f"Created: {title}"))
            return True
        else:
            print(colors.red("Failed to create note."))
            return False
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def edit_note(title: str) -> bool:
    """Open a note in $EDITOR for editing."""
    note_id = _resolve_id(title)
    if note_id is None:
        print(colors.red(f"Note not found: {title}"))
        return False

    html = read_note_html_by_id(note_id)
    if html is None:
        print(colors.red(f"Note not found: {title}"))
        return False

    editor = os.environ.get("EDITOR", "vim")
    md_content = convert.html_to_md(html)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", prefix="simple-memo-", delete=False
    ) as f:
        f.write(md_content)
        tmp_path = f.name

    try:
        subprocess.run([editor, tmp_path], check=True)
        new_content = Path(tmp_path).read_text().strip()

        if new_content == md_content.strip():
            print(colors.yellow("No changes — edit cancelled."))
            return False

        new_html = convert.md_to_html(new_content)
        esc_id = osa_escape(note_id)
        esc_html = osa_escape(new_html)

        script = f'''
            tell application "Notes"
                set theNote to first note whose id is "{esc_id}"
                set body of theNote to "{esc_html}"
            end tell
        '''
        result = run(script)
        if result.startswith("error:"):
            print(colors.red("Failed to save changes."))
            return False

        print(colors.green(f"Updated: {title}"))
        return True
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def append_note(title: str, text: str) -> bool:
    """Append text (Markdown) to an existing note."""
    note_id = _resolve_id(title)
    if note_id is None:
        print(colors.red(f"Note not found: {title}"))
        return False

    esc_id = osa_escape(note_id)
    html_text = convert.md_to_html(text)
    esc_html = osa_escape(html_text)

    script = f'''
        tell application "Notes"
            set theNote to first note whose id is "{esc_id}"
            set body of theNote to (body of theNote) & "{esc_html}"
        end tell
    '''
    result = run(script)
    if result.startswith("error:"):
        print(colors.red(f"Note not found: {title}"))
        return False
    print(colors.green(f"Appended to: {title}"))
    return True


def delete_note(title: str) -> bool:
    """Delete a note by title (resolves to ID internally to avoid confirmation dialog)."""
    note_id = _resolve_id(title)
    if note_id is None:
        print(colors.red(f"Note not found: {title}"))
        return False
    return delete_note_by_id(note_id, title)


def delete_note_by_id(note_id: str, label: str = "") -> bool:
    """Delete a note by its internal ID (no confirmation dialog)."""
    esc = osa_escape(note_id)
    script = f'''
        tell application "Notes"
            set theNote to first note whose id is "{esc}"
            delete theNote
        end tell
    '''
    result = run(script)
    if result.startswith("error:"):
        print(colors.red(f"Failed to delete: {label or note_id}"))
        return False
    print(colors.green(f"Deleted: {label or note_id}"))
    return True


def _resolve_id(title: str) -> str | None:
    """Look up a note's internal ID by title."""
    esc = osa_escape(title)
    script = f'''
        tell application "Notes"
            set matchedNotes to (notes whose name is "{esc}")
            if (count of matchedNotes) is 0 then
                return "error:not_found"
            end if
            return id of item 1 of matchedNotes
        end tell
    '''
    result = run(script)
    if result.startswith("error:"):
        return None
    return result.strip()


def move_note(title: str, target_folder: str) -> bool:
    """Move a note to a different folder (creates folder if needed)."""
    note_id = _resolve_id(title)
    if note_id is None:
        print(colors.red(f"Note not found: {title}"))
        return False

    esc_id = osa_escape(note_id)
    esc_folder = osa_escape(target_folder)

    script = f'''
        tell application "Notes"
            set theNote to first note whose id is "{esc_id}"
            try
                set targetFolder to folder "{esc_folder}"
            on error
                make new folder with properties {{name:"{esc_folder}"}}
                set targetFolder to folder "{esc_folder}"
            end try
            move theNote to targetFolder
            return "moved"
        end tell
    '''
    result = run(script)
    if result.startswith("error:"):
        print(colors.red(f"Failed to move: {title}"))
        return False
    print(colors.green(f"Moved '{title}' to folder '{target_folder}'"))
    return True


def create_folder(name: str) -> bool:
    """Create a new folder in Apple Notes."""
    esc = osa_escape(name)
    script = f'''
        tell application "Notes"
            make new folder with properties {{name:"{esc}"}}
            return "created"
        end tell
    '''
    result = run(script)
    if result.startswith("error:"):
        print(colors.red(f"Failed to create folder: {name}"))
        return False
    print(colors.green(f"Created folder: {name}"))
    return True


def delete_folder(name: str) -> bool:
    """Delete a folder from Apple Notes (by ID to avoid confirmation dialog)."""
    esc_name = osa_escape(name)
    # Resolve folder ID first
    script = f'''
        tell application "Notes"
            set matchedFolders to (folders whose name is "{esc_name}")
            if (count of matchedFolders) is 0 then
                return "error:not_found"
            end if
            return id of item 1 of matchedFolders
        end tell
    '''
    result = run(script)
    if result.startswith("error:"):
        print(colors.red(f"Folder not found: {name}"))
        return False

    folder_id = result.strip()
    esc_id = osa_escape(folder_id)
    del_script = f'''
        tell application "Notes"
            set theFolder to first folder whose id is "{esc_id}"
            delete theFolder
        end tell
    '''
    result = run(del_script)
    if result.startswith("error:"):
        print(colors.red(f"Failed to delete folder: {name}"))
        return False
    print(colors.green(f"Deleted folder: {name}"))
    return True


def search_notes(query: str) -> list[dict]:
    """Search notes by content or title. Returns matching notes."""
    esc = osa_escape(query)
    # Iterate all notes, check title and body.
    # Using `try` around plaintext to handle edge cases.
    script = f'''
        tell application "Notes"
            set output to ""
            repeat with n in every note
                set t to name of n
                set matched to false
                if t contains "{esc}" then
                    set matched to true
                else
                    try
                        set b to plaintext of n
                        if b contains "{esc}" then
                            set matched to true
                        end if
                    end try
                end if
                if matched then
                    set fName to ""
                    try
                        set fName to name of container of n
                    end try
                    set output to output & id of n & "|" & t & "|" & fName & linefeed
                end if
            end repeat
            return output
        end tell
    '''
    raw = run(script)
    if raw.startswith("error:"):
        return []

    results = []
    seen = set()
    for line in raw.strip().splitlines():
        parts = line.split("|", 2)
        if len(parts) < 3:
            continue
        nid, title, folder = parts[0].strip(), parts[1].strip(), parts[2].strip()
        if folder.lower() in TRASH_NAMES or nid in seen:
            continue
        seen.add(nid)
        results.append({"id": nid, "title": title, "folder": folder})
    return results


def fuzzy_search() -> None:
    """Interactive fuzzy search using fzf (if available)."""
    if not shutil.which("fzf"):
        print(colors.yellow("fzf not installed. Install: brew install fzf"))
        print("Falling back to simple search.")
        query = input("Search query: ").strip()
        if query:
            results = search_notes(query)
            _print_notes_list(results)
        return

    notes = list_notes()
    if not notes:
        print("No notes found.")
        return

    lines = [f"{n['folder']} — {n['title']}" for n in notes]
    input_text = "\n".join(lines)

    try:
        result = subprocess.run(
            ["fzf", "--height=40%", "--border", "--prompt=Search notes: "],
            input=input_text,
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout.strip():
            selected = result.stdout.strip()
            # Extract title after " — "
            if " — " in selected:
                title = selected.split(" — ", 1)[1]
                content = read_note(title)
                if content:
                    print(f"\n{colors.bold(title)}\n")
                    print(content)
    except KeyboardInterrupt:
        pass


def count_notes() -> int:
    """Count total notes."""
    script = '''
        tell application "Notes"
            return count of every note
        end tell
    '''
    raw = run(script)
    try:
        return int(raw)
    except ValueError:
        return 0


def export_notes(output_dir: str | None = None, as_markdown: bool = True) -> int:
    """Export all notes to files. Returns count of exported notes."""
    if output_dir is None:
        output_dir = str(Path.home() / "Desktop" / "simple-memo-export")

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    notes = list_notes()
    exported = 0

    for note in notes:
        html = read_note_html(note["title"])
        if html is None:
            continue

        # Sanitize filename
        safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in note["title"])
        safe_name = safe_name[:100].strip()

        if as_markdown:
            content = convert.html_to_md(html)
            ext = ".md"
        else:
            content = html
            ext = ".html"

        # Put in subfolder by Notes folder
        folder_dir = out_path / note["folder"]
        folder_dir.mkdir(parents=True, exist_ok=True)
        filepath = folder_dir / f"{safe_name}{ext}"

        filepath.write_text(content, encoding="utf-8")
        exported += 1

    return exported


def _print_notes_list(notes: list[dict]) -> None:
    """Pretty-print a numbered list of notes."""
    if not notes:
        print("No notes found.")
        return
    for i, n in enumerate(notes, 1):
        folder = colors.dim(n["folder"])
        print(f"  {colors.cyan(str(i))}. {folder} — {n['title']}")
