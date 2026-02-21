"""Markdown <-> HTML conversion utilities."""

import mistune
import html2text


def md_to_html(markdown_text: str) -> str:
    """Convert Markdown to HTML for Apple Notes storage."""
    return mistune.html(markdown_text)


def html_to_md(html_content: str) -> str:
    """Convert HTML from Apple Notes to Markdown for display/editing."""
    h = html2text.HTML2Text()
    h.body_width = 0  # No line wrapping
    h.ignore_images = False
    h.ignore_links = False
    return h.handle(html_content).strip()
