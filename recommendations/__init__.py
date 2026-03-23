"""
recommendations — Generate a titles index from the vault and deduplicate
                  the "Notes to write" list against it.

Run interactively:
    python -m recommendations

Import individual functions:
    from recommendations import write_titles, remove_duplicates
"""

from .core import remove_duplicates, write_titles

__all__ = ["write_titles", "remove_duplicates"]
