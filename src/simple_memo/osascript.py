"""AppleScript execution helpers."""

import subprocess
import sys


def run(script: str, timeout: int = 30) -> str:
    """Execute an AppleScript and return stdout. Exit on error."""
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return "error: timeout"
    if result.returncode != 0:
        # Some AppleScript errors are expected (e.g. "not found").
        # Return stderr so the caller can inspect it.
        return f"error: {result.stderr.strip()}"
    return result.stdout.strip()


def require_macos() -> None:
    """Exit immediately if not running on macOS."""
    if sys.platform != "darwin":
        print("error: simple-memo requires macOS (Apple Notes & Reminders)")
        sys.exit(1)


def osa_escape(text: str) -> str:
    """Escape a string for safe embedding in AppleScript double-quoted strings."""
    return text.replace("\\", "\\\\").replace('"', '\\"')
