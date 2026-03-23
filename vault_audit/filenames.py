import re
from pathlib import Path

from . import state
from .aliases import get_all_aliases_for_note, save_aliases
from .io import get_all_notes, read_note, write_note
from .utils import clear_screen


def is_acronym(stem: str) -> bool:
    """True if stem is 2+ uppercase letters with no spaces (e.g. CNN, ASCII)."""
    return bool(re.fullmatch(r"[A-Z]{2,}", stem))


def proposed_filename(stem: str) -> "str | None":
    """
    Propose a cleaned, title-cased filename stem.
    Returns None if the result is identical to the input stem.
    """
    cleaned = stem.replace("-", " ").replace("_", " ")
    cleaned = re.sub(r"[^\w\s]", "", cleaned).replace("_", " ")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    cleaned = cleaned.title()
    return None if cleaned == stem else cleaned


def detect_corruption(path: Path) -> "str | None":
    """Return a human-readable corruption reason, or None if the file is clean."""
    from .io import parse_frontmatter
    try:
        if path.stat().st_size == 0:
            return "empty file (0 bytes)"
        raw = read_note(path)
        if raw is None:
            return "unreadable (encoding error)"
        parse_frontmatter(raw)
        return None
    except ValueError as e:
        return f"malformed YAML frontmatter: {e}"


def update_wikilinks_for_rename(old_stem: str, new_stem: str, all_notes: list) -> int:
    """
    Replace [[OldStem]] and [[OldStem|alias]] with [[NewStem]] and [[NewStem|alias]]
    in every note. Case-insensitive. Returns count of modified files.
    """
    pattern = re.compile(
        r"\[\[" + re.escape(old_stem) + r"(\|[^\]]+)?\]\]",
        flags=re.IGNORECASE,
    )
    modified = 0
    for path in all_notes:
        raw = read_note(path)
        if raw is None:
            continue
        new_raw = pattern.sub(lambda m: f"[[{new_stem}{m.group(1) or ''}]]", raw)
        if new_raw != raw:
            write_note(path, new_raw)
            modified += 1
    return modified


def collect_filename_issues(notes: list) -> tuple:
    """
    Read-only scan. Returns (renames, acronyms, corrupted).
    Renames that would collide on the same proposed stem are excluded with a warning.
    """
    renames = []
    acronyms = []
    corrupted = []
    collision_map: dict = {}

    for path in notes:
        reason = detect_corruption(path)
        if reason:
            corrupted.append((path, reason))
            continue
        if is_acronym(path.stem):
            acronyms.append(path)
            continue
        proposed = proposed_filename(path.stem)
        if proposed:
            collision_map.setdefault(proposed, []).append(path)

    for proposed, paths in collision_map.items():
        if len(paths) > 1:
            print(f"\n  [!] Rename collision — multiple files normalise to '{proposed}.md':")
            for p in paths:
                print(f"        {p.name}")
            print("      All skipped — resolve manually.")
        else:
            renames.append((paths[0], proposed))

    return renames, acronyms, corrupted


def run_filename_validation() -> None:
    """Menu Option 1: interactively validate and fix note filenames."""
    clear_screen()
    print("\n── Option 1: Filename Validation ────────────────────────────────────")
    notes = get_all_notes()
    if not notes:
        print("  No notes found in ./notes/")
        input("\nPress Enter to return to menu...")
        return

    renames, acronyms, corrupted = collect_filename_issues(notes)

    print(f"\nCorrupted files ({len(corrupted)}):", end="")
    if corrupted:
        print()
        for path, reason in corrupted:
            print(f"    {path.name}  [{reason}]")
    else:
        print("  none")

    print(f"\nAcronyms flagged for manual review ({len(acronyms)}):", end="")
    if acronyms:
        print()
        print("    " + "  ".join(p.name for p in acronyms))
    else:
        print("  none")

    if not renames:
        print("\nProposed renames: none  (all filenames are valid)")
        input("\nPress Enter to return to menu...")
        return

    print(f"\nProposed renames ({len(renames)}):")
    for i, (path, proposed) in enumerate(renames, 1):
        suffix = "  [possible duplicate — consider running Option 2]" if "(1)" in path.stem else ""
        print(f"  [{i:3}] {path.name:<55} ->  {proposed}.md{suffix}")

    print("\nApply? [y=all  |  N=cancel  |  1,3,5=apply selected]: ", end="")
    choice = input().strip().lower()

    if not choice or choice == "n":
        print("  Cancelled.")
        input("\nPress Enter to return to menu...")
        return

    if choice == "y":
        selected_indices = list(range(len(renames)))
    else:
        try:
            selected_indices = [int(x.strip()) - 1 for x in choice.split(",")]
            selected_indices = [i for i in selected_indices if 0 <= i < len(renames)]
        except ValueError:
            print("  Invalid input. Cancelled.")
            input("\nPress Enter to return to menu...")
            return

    applied = 0
    for i in selected_indices:
        path, proposed = renames[i]
        new_path = path.parent / f"{proposed}.md"
        case_only = path.name.lower() == new_path.name.lower()
        if not case_only and new_path.exists():
            print(f"  [!] Skipping '{path.name}' — target '{new_path.name}' already exists.")
            continue
        old_stem = path.stem
        if case_only:
            # Windows case-insensitive filesystem: rename via temp name to force case change
            tmp_path = path.parent / f"{path.stem}__tmp_rename__.md"
            path.rename(tmp_path)
            tmp_path.rename(new_path)
        else:
            path.rename(new_path)
        fresh_notes = get_all_notes()
        n = update_wikilinks_for_rename(old_stem, proposed, fresh_notes)
        if old_stem in state.ALIASES:
            entry = state.ALIASES.pop(old_stem)
            state.ALIASES[proposed] = entry
            if old_stem in entry["aliases"]:
                entry["aliases"].remove(old_stem)
            if proposed not in entry["aliases"]:
                entry["aliases"].insert(0, proposed)
        print(f"  Renamed: {path.name}  ->  {new_path.name}  ({n} wikilink file(s) updated)")
        applied += 1

    save_aliases()
    print(f"\n  Done. {applied}/{len(selected_indices)} rename(s) applied.")
    input("\nPress Enter to return to menu...")
