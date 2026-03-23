"""
keywords — Extract top unigrams, bigrams, and trigrams from a markdown note directory.

Run interactively:
    python -m keywords

Import the extractor:
    from keywords import extract_keywords
    results = extract_keywords("./notes")
"""

from .extractor import extract_keywords

__all__ = ["extract_keywords"]
