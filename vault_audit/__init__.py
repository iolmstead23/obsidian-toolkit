"""
vault_audit — Obsidian vault audit and maintenance package.

Run interactively:
    python -m vault_audit

Import individual features:
    from vault_audit.filenames import run_filename_validation
    from vault_audit.duplicates import run_duplicate_detection
    from vault_audit.unlinked import run_unlinked_references, find_unlinked_references
    from vault_audit.report import run_generate_report
    from vault_audit.aliases import load_aliases, build_aliases_from_vault
"""

from .aliases import build_aliases_from_vault, load_aliases, save_aliases
from .duplicates import run_duplicate_detection
from .filenames import run_filename_validation
from .report import run_generate_report
from .unlinked import find_unlinked_references, run_unlinked_references

__all__ = [
    "load_aliases",
    "save_aliases",
    "build_aliases_from_vault",
    "run_filename_validation",
    "run_duplicate_detection",
    "run_unlinked_references",
    "find_unlinked_references",
    "run_generate_report",
]
