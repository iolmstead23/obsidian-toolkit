"""
Entry point: python -m vault_audit
"""
from .aliases import build_aliases_from_vault, load_aliases
from .constants import ALIASES_FILE, OUTPUT_DIR
from .duplicates import run_duplicate_detection
from .filenames import run_filename_validation
from .report import run_generate_report
from .unlinked import run_unlinked_references
from .utils import clear_screen
from . import state

MENU = """
╔══════════════════════════════════════════════╗
║        Obsidian Vault Audit Tool             ║
╠══════════════════════════════════════════════╣
║  1. Validate Filenames & Fix Corruption      ║
║  2. Detect Duplicates (Cosine Similarity)    ║
║  3. Discover Unlinked References             ║
║  4. Generate Report                          ║
║  5. Build / Refresh Alias Map                ║
║  6. Exit                                     ║
╚══════════════════════════════════════════════╝"""


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    load_aliases()
    entry_count = len(state.ALIASES)
    if entry_count:
        print(f"  Loaded {entry_count} alias entries from {ALIASES_FILE.name}")
    else:
        print("  No alias file found — run Option 5 to build the alias map.")

    dispatch = {
        "1": run_filename_validation,
        "2": run_duplicate_detection,
        "3": run_unlinked_references,
        "4": run_generate_report,
        "5": lambda: (clear_screen(), build_aliases_from_vault()),
        "6": lambda: None,
    }

    while True:
        clear_screen()
        print(MENU)
        choice = input("\nSelect option: ").strip()
        if choice == "6":
            print("  Goodbye.")
            break
        if choice in dispatch:
            dispatch[choice]()
        else:
            print("  Invalid choice — enter 1 through 6.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted. Goodbye.")
