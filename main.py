#!/usr/bin/env python3
"""
main.py — Obsidian Knowledge Tools
Unified frontend for vault_audit, keywords, and recommendations packages.

Usage:
    python main.py
"""
from pathlib import Path

from keywords.extractor import extract_keywords
from recommendations.core import (
    NOTES_TO_WRITE,
    TITLES_FILE,
    remove_duplicates,
    write_titles,
)
from vault_audit import state
from vault_audit.aliases import build_aliases_from_vault, load_aliases
from vault_audit.constants import ALIASES_FILE, OUTPUT_DIR
from vault_audit.duplicates import run_duplicate_detection
from vault_audit.filenames import run_filename_validation
from vault_audit.report import run_generate_report
from vault_audit.unlinked import run_unlinked_references
from vault_audit.utils import clear_screen

KEYWORDS_REPORT = OUTPUT_DIR / "keyword report.txt"

MENU = """
╔══════════════════════════════════════════════════════╗
║            Obsidian Knowledge Tools                  ║
╠══════════════════════════════════════════════════════╣
║  ── Vault Audit ───────────────────────────────────  ║
║   1.  Validate Filenames & Fix Corruption            ║
║   2.  Detect Duplicates  (Cosine Similarity)         ║
║   3.  Discover Unlinked References                   ║
║   4.  Generate Audit Report                          ║
║   5.  Build / Refresh Alias Map                      ║
║  ── Keywords ──────────────────────────────────────  ║
║   6.  Extract Keywords from Notes                    ║
║  ── Recommendations ───────────────────────────────  ║
║   7.  Refresh Titles & Deduplicate Write Queue       ║
║  ─────────────────────────────────────────────────   ║
║   0.  Exit                                           ║
╚══════════════════════════════════════════════════════╝"""


# ---------------------------------------------------------------------------
# Keywords runner
# ---------------------------------------------------------------------------

def run_keywords() -> None:
    clear_screen()
    print("\n── Keywords: Extract from Notes ──────────────────────────────────────")
    print("  Scanning ./notes/ ...")

    keywords = extract_keywords("./notes")

    if not any(keywords.values()):
        print("  No keywords found — check that ./notes/ contains .md files.")
        input("\nPress Enter to return to menu...")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(KEYWORDS_REPORT, "w", encoding="utf-8") as f:
        f.write("Top 20 Trigrams (Three Word Phrases):\n")
        f.write("=====================================\n\n")
        for phrase, count in keywords["trigrams"]:
            f.write(f"{phrase} ---- {count}\n")

        f.write("\nTop 20 Bigrams (Two Word Phrases):\n")
        f.write("==================================\n\n")
        for phrase, count in keywords["bigrams"]:
            f.write(f"{phrase} ---- {count}\n")

        f.write("\nTop 20 Unigrams (Single Words):\n")
        f.write("==============================\n\n")
        for word, count in keywords["unigrams"]:
            f.write(f"{word} ---- {count}\n")

    # Show preview on screen
    def _preview(label: str, items: list) -> None:
        print(f"\n  {label}:")
        if items:
            for phrase, count in items[:5]:
                print(f"    {phrase}  ({count})")
            if len(items) > 5:
                print(f"    ... and {len(items) - 5} more")
        else:
            print("    (none)")

    _preview("Top Trigrams", keywords["trigrams"])
    _preview("Top Bigrams",  keywords["bigrams"])
    _preview("Top Unigrams", keywords["unigrams"])

    print(f"\n  Full report saved to {KEYWORDS_REPORT}")
    input("\nPress Enter to return to menu...")


# ---------------------------------------------------------------------------
# Recommendations runner
# ---------------------------------------------------------------------------

def run_recommendations() -> None:
    clear_screen()
    print("\n── Recommendations: Titles & Write Queue ─────────────────────────────")

    titles = write_titles()
    print(f"  Titles indexed: {len(titles)} note(s)  ->  {TITLES_FILE}")

    if not NOTES_TO_WRITE.exists():
        print(f"\n  '{NOTES_TO_WRITE.name}' not found — nothing to deduplicate.")
        input("\nPress Enter to return to menu...")
        return

    removed, remaining = remove_duplicates()
    print(f"  Removed {removed} duplicate(s) from '{NOTES_TO_WRITE.name}'")
    print(f"  Remaining entries to write: {remaining}")

    input("\nPress Enter to return to menu...")


# ---------------------------------------------------------------------------
# Main menu loop
# ---------------------------------------------------------------------------

def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    load_aliases()
    entry_count = len(state.ALIASES)
    if entry_count:
        print(f"  Loaded {entry_count} alias entries from {ALIASES_FILE.name}")
    else:
        print("  No alias file found — run option 5 to build the alias map.")

    dispatch = {
        "1": run_filename_validation,
        "2": run_duplicate_detection,
        "3": run_unlinked_references,
        "4": run_generate_report,
        "5": lambda: (clear_screen(), build_aliases_from_vault()),
        "6": run_keywords,
        "7": run_recommendations,
    }

    while True:
        clear_screen()
        print(MENU)
        choice = input("\nSelect option: ").strip()
        if choice == "0":
            print("  Goodbye.")
            break
        if choice in dispatch:
            dispatch[choice]()
        else:
            print("  Invalid choice — enter 0 through 7.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted. Goodbye.")
