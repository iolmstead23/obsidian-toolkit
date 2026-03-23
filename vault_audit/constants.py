from pathlib import Path

NOTES_DIR            = Path("./notes")
DUPLICATES_DIR       = NOTES_DIR / "_duplicates"
OUTPUT_DIR           = Path("./output")
ALIASES_FILE         = Path("./aliases.json")
REPORT_FILE          = OUTPUT_DIR / "vault_report.md"
SIMILARITY_THRESHOLD = 0.85
MODEL_NAME           = "all-MiniLM-L6-v2"
EXCLUDE_DIRS         = frozenset({".obsidian", "_duplicates"})
