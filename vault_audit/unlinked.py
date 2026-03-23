import re
from pathlib import Path

from . import state
from .aliases import build_aliases_from_vault
from .io import get_all_notes, read_note, write_note
from .utils import clear_screen


def _get_excluded_zones(raw: str) -> list:
    """
    Return list of (start, end) char ranges to exclude from link matching:
    frontmatter, fenced code, inline code, math, and existing [[wikilinks]].
    """
    zones = []
    m = re.match(r"^---\r?\n.*?\r?\n---\r?\n?", raw, re.DOTALL)
    if m:
        zones.append((0, m.end()))
    for m in re.finditer(r"```[\s\S]*?```", raw):
        zones.append((m.start(), m.end()))
    for m in re.finditer(r"`[^`]*`", raw):
        zones.append((m.start(), m.end()))
    # Block math ($$...$$) before inline math ($...$) to avoid partial matches
    for m in re.finditer(r"\$\$[\s\S]*?\$\$", raw):
        zones.append((m.start(), m.end()))
    for m in re.finditer(r"\$[^$\n]+?\$", raw):
        zones.append((m.start(), m.end()))
    for m in re.finditer(r"\[\[.*?\]\]", raw):
        zones.append((m.start(), m.end()))
    return zones


def _build_search_forms(notes: list) -> list:
    """
    Build a list of (form_str, canonical_stem) for all note names and aliases,
    sorted by form length descending (longer forms take priority in matching).
    Minimum form length: 4 characters.
    """
    forms = []
    indexed_stems = set()

    for stem, data in state.ALIASES.items():
        indexed_stems.add(stem)
        for alias in data.get("aliases", []):
            if len(alias) >= 4:
                forms.append((alias, stem))

    for path in notes:
        s = path.stem
        if s not in indexed_stems and len(s) >= 4:
            forms.append((s, s))

    forms.sort(key=lambda x: len(x[0]), reverse=True)
    return forms


def _form_is_canonical_prefix(form: str, canonical: str, raw: str, match_end: int) -> bool:
    """
    Returns True when 'form' is a strict prefix of 'canonical' (treating hyphens
    and spaces as equivalent) AND the remaining canonical words appear immediately
    after match_end in the raw text.

    Example: form="Breadth-First", canonical="Breadth First Search",
             raw[match_end:] starts with " Search" -> True.
    This means the full note title is already written out; the alias match is
    redundant and should be skipped.
    """
    form_norm = re.sub(r"[-\s]+", " ", form).strip().lower()
    canonical_norm = re.sub(r"[-\s]+", " ", canonical).strip().lower()
    if not canonical_norm.startswith(form_norm + " "):
        return False
    remaining = canonical_norm[len(form_norm):].strip()
    rest_pattern = r"[\s\-]+" + r"[\s\-]+".join(re.escape(w) for w in remaining.split())
    return bool(re.match(rest_pattern, raw[match_end: match_end + len(remaining) + 10], re.IGNORECASE))


def find_unlinked_references(note_path: Path, forms: list) -> list:
    """
    Scan a note for plain-text occurrences of note names/aliases that are not
    already wrapped in [[wikilinks]] or inside excluded zones.

    Returns list of (matched_surface, canonical_stem, start_pos_in_raw).
    """
    raw = read_note(note_path)
    if raw is None:
        return []

    note_stem = note_path.stem
    stem_lower = note_stem.lower()
    zones = _get_excluded_zones(raw)

    # Build a masked copy: same length as raw, excluded zones replaced with spaces.
    chars = list(raw)
    for z_start, z_end in zones:
        for i in range(z_start, min(z_end, len(chars))):
            chars[i] = " "
    masked = "".join(chars)

    found = []
    seen_ranges: list = []

    for form, canonical in forms:
        # Skip self-references (case-insensitive)
        if canonical.lower() == stem_lower:
            continue
        # Skip forms that are sub-phrases of this note's own title.
        # e.g. don't suggest linking "software" inside "System Software.md"
        if re.search(r"\b" + re.escape(form.lower()) + r"\b", stem_lower):
            continue
        pattern = re.compile(r"\b" + re.escape(form) + r"\b", re.IGNORECASE)
        for m in re.finditer(pattern, masked):
            start, end = m.start(), m.end()
            if any(start < r_end and end > r_start for r_start, r_end in seen_ranges):
                continue
            # Skip partial alias matches where the full canonical title follows immediately.
            # e.g. "Breadth-First" inside "Breadth-First Search (BFS)"
            if _form_is_canonical_prefix(form, canonical, raw, end):
                seen_ranges.append((start, end))
                continue
            seen_ranges.append((start, end))
            found.append((raw[start:end], canonical, start))

    return found


def run_unlinked_references() -> None:
    """Menu Option 3: discover plain-text references that could be wikilinks."""
    clear_screen()
    print("\n── Option 3: Unlinked Reference Discovery ───────────────────────────")

    if not state.ALIASES:
        print("  Alias map is empty. Building from vault first...")
        build_aliases_from_vault()

    notes = get_all_notes()
    if not notes:
        print("  No notes found.")
        input("\nPress Enter to return to menu...")
        return

    forms = _build_search_forms(notes)
    total_inserted = 0
    total_modified = 0

    for note_path in notes:
        matches = find_unlinked_references(note_path, forms)
        if not matches:
            continue

        raw = read_note(note_path)
        if raw is None:
            continue

        print(f"\n  ── {note_path.name}  ({len(matches)} potential link(s)) ──")
        confirmed = []
        skip_note = False

        for surface, canonical, start in matches:
            ctx_start = max(0, start - 50)
            ctx_end   = min(len(raw), start + len(surface) + 50)
            ctx = raw[ctx_start:ctx_end].replace("\n", " ")
            rel = start - ctx_start
            highlighted = (
                ctx[:rel]
                + ">>>" + ctx[rel : rel + len(surface)] + "<<<"
                + ctx[rel + len(surface):]
            )
            print(f"\n    '{surface}'  ->  [[{canonical}]]")
            print(f"    ...{highlighted}...")
            print("    Insert? [y/N/s=skip rest of note]: ", end="")
            ans = input().strip().lower()

            if ans == "s":
                skip_note = True
                break
            if ans == "y":
                confirmed.append((start, len(surface), canonical, surface))

        if confirmed and not skip_note:
            raw_list = list(raw)
            for start, length, canonical, surface in sorted(confirmed, key=lambda x: x[0], reverse=True):
                if surface.lower() == canonical.lower():
                    link = f"[[{canonical}]]"
                else:
                    link = f"[[{canonical}|{surface}]]"
                raw_list[start : start + length] = list(link)
            write_note(note_path, "".join(raw_list))
            total_inserted += len(confirmed)
            total_modified += 1
            print(f"    -> {len(confirmed)} link(s) inserted in {note_path.name}")

    print(f"\n  Done. {total_inserted} link(s) inserted across {total_modified} note(s).")
    input("\nPress Enter to return to menu...")
