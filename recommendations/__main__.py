"""
Entry point: python -m recommendations

1. Rebuilds output/titles.txt from ./notes/
2. Removes entries in "Notes to write.md" that already exist as notes.
"""
from .core import NOTES_TO_WRITE, TITLES_FILE, remove_duplicates, write_titles


def main() -> None:
    print("── Recommendations ──────────────────────────────────────────────────")

    # Step 1: rebuild titles index
    titles = write_titles()
    print(f"  Titles indexed: {len(titles)} notes -> {TITLES_FILE}")

    # Step 2: deduplicate notes-to-write list
    if not NOTES_TO_WRITE.exists():
        print(f"  '{NOTES_TO_WRITE.name}' not found — nothing to deduplicate.")
    else:
        removed, remaining = remove_duplicates()
        print(f"  Removed {removed} duplicate entries from '{NOTES_TO_WRITE.name}'")
        print(f"  Remaining entries: {remaining}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        input("\nPress Enter to exit...")
