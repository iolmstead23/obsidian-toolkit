import re
from pathlib import Path

import yaml

from .constants import EXCLUDE_DIRS, NOTES_DIR


def get_all_notes() -> list:
    """Return all .md Paths under NOTES_DIR, excluding EXCLUDE_DIRS subdirectories."""
    notes = []
    for path in NOTES_DIR.rglob("*.md"):
        if any(part in EXCLUDE_DIRS for part in path.parts):
            continue
        notes.append(path)
    return sorted(notes)


def read_note(path: Path) -> "str | None":
    """
    Read raw text of a note.
    Returns None if the file is 0 bytes or cannot be decoded as UTF-8.
    Uses utf-8-sig to silently strip BOMs.
    """
    try:
        if path.stat().st_size == 0:
            return None
        return path.read_text(encoding="utf-8-sig")
    except (UnicodeDecodeError, OSError):
        return None


def parse_frontmatter(raw: str) -> tuple:
    """
    Split raw content into (frontmatter_dict, body_text).
    Returns ({}, raw) if no frontmatter delimiters are found.
    Raises ValueError if the YAML block is malformed.
    """
    if not raw.startswith("---"):
        return {}, raw
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?", raw, re.DOTALL)
    if not m:
        return {}, raw
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        raise ValueError(str(e))
    return fm, raw[m.end():]


def strip_markdown_for_text(raw: str) -> str:
    """
    Return plain text suitable for embedding or token matching.
    Strips frontmatter, code blocks, math, wikilinks, and HTML.
    """
    t = raw
    t = re.sub(r"^---\r?\n.*?\r?\n---\r?\n?", "", t, flags=re.DOTALL)
    t = re.sub(r"```[\s\S]*?```", "", t)
    t = re.sub(r"`[^`]*`", "", t)
    t = re.sub(r"\${1,2}[^$]*\${1,2}", "", t)
    t = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", t)
    t = re.sub(r"\[\[([^\]]+)\]\]", r"\1", t)
    t = re.sub(r"<[^>]*>", "", t)
    t = re.sub(r"^#{1,6}\s+", "", t, flags=re.MULTILINE)
    t = re.sub(r"\*{1,3}([^*\n]+)\*{1,3}", r"\1", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def extract_wikilinks(raw: str) -> list:
    """Return list of (target, alias_or_None) tuples from [[...]] syntax."""
    return [
        (m.group(1).strip(), m.group(2).strip() if m.group(2) else None)
        for m in re.finditer(r"\[\[([^\]|]+?)(?:\|([^\]]+?))?\]\]", raw)
    ]


def write_note(path: Path, content: str) -> None:
    """Write content back to a note file using UTF-8 encoding."""
    path.write_text(content, encoding="utf-8")
