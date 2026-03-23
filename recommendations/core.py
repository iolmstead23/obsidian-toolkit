import os
from pathlib import Path

NOTES_DIR       = Path("./notes")
OUTPUT_DIR      = Path("./output")
TITLES_FILE     = OUTPUT_DIR / "titles.txt"
NOTES_TO_WRITE  = Path("./Notes to write.md")


# ---------------------------------------------------------------------------
# Title generation (from Titles.py)
# ---------------------------------------------------------------------------

def write_titles(notes_dir: Path = NOTES_DIR) -> list:
    """
    Scan notes_dir for .md files and write their stems (filenames without
    extension) to output/titles.txt, one per line.

    Returns the list of title strings written.
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    titles = []
    if notes_dir.exists():
        for name in os.listdir(notes_dir):
            if name.endswith((".md", ".markdown")):
                titles.append(Path(name).stem)
    else:
        print(f"  Notes directory not found: {notes_dir}")

    with open(TITLES_FILE, "w", encoding="utf-8") as f:
        for title in sorted(titles):
            f.write(f"{title}\n")

    return titles


# ---------------------------------------------------------------------------
# Duplicate removal (from GenerateRecommendations.py)
# ---------------------------------------------------------------------------

def _read_lines(file_path: Path) -> set:
    """Read a text file into a set of non-empty stripped lines."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return {line.strip() for line in f if line.strip()}
    except FileNotFoundError:
        print(f"  Creating new file: {file_path}")
        file_path.touch()
        return set()


def _write_lines(file_path: Path, entries: set) -> None:
    """Write a sorted set of strings to a file, one per line."""
    with open(file_path, "w", encoding="utf-8") as f:
        for entry in sorted(entries):
            f.write(f"{entry}\n")


def remove_duplicates(
    notes_to_write: Path = NOTES_TO_WRITE,
    titles_file: Path = TITLES_FILE,
) -> tuple:
    """
    Remove entries from notes_to_write that already exist in titles_file.

    Returns (removed_count, remaining_count).
    """
    existing_titles = _read_lines(titles_file)
    candidates = _read_lines(notes_to_write)

    unique = candidates - existing_titles
    removed = len(candidates) - len(unique)

    _write_lines(notes_to_write, unique)
    return removed, len(unique)
