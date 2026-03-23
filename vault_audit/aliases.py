import json
import shutil

from . import state
from .constants import ALIASES_FILE
from .io import extract_wikilinks, get_all_notes, parse_frontmatter, read_note


def load_aliases() -> None:
    """
    Load ALIASES_FILE into the shared state.ALIASES dict.
    Creates an empty dict if the file is missing.
    On malformed JSON: backs up the file and starts fresh.
    """
    if not ALIASES_FILE.exists():
        state.ALIASES.clear()
        return
    try:
        data = json.loads(ALIASES_FILE.read_text(encoding="utf-8"))
        state.ALIASES.clear()
        state.ALIASES.update(data)
    except json.JSONDecodeError:
        bak = ALIASES_FILE.with_suffix(".json.bak")
        shutil.copy(ALIASES_FILE, bak)
        print(f"  [!] aliases.json was malformed — backed up to {bak.name}, starting fresh.")
        state.ALIASES.clear()


def save_aliases() -> None:
    """Write state.ALIASES to ALIASES_FILE as formatted JSON."""
    ALIASES_FILE.write_text(
        json.dumps(state.ALIASES, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def build_aliases_from_vault() -> None:
    """
    Scan all notes; extract YAML aliases: fields and [[Target|DisplayText]]
    inline aliases. Merges into state.ALIASES and saves to disk.
    """
    for path in get_all_notes():
        stem = path.stem
        raw = read_note(path)
        if raw is None:
            continue

        entry = state.ALIASES.setdefault(stem, {"aliases": []})
        if stem not in entry["aliases"]:
            entry["aliases"].insert(0, stem)

        try:
            fm, _ = parse_frontmatter(raw)
        except ValueError:
            fm = {}
        fm_aliases = fm.get("aliases", [])
        if isinstance(fm_aliases, str):
            fm_aliases = [fm_aliases]
        for a in fm_aliases or []:
            if a and a not in entry["aliases"]:
                entry["aliases"].append(a)

        for target, alias in extract_wikilinks(raw):
            if alias and target in state.ALIASES:
                t_entry = state.ALIASES[target]
                if alias not in t_entry["aliases"]:
                    t_entry["aliases"].append(alias)

    save_aliases()
    print(f"  Alias map built: {len(state.ALIASES)} notes indexed.")


def get_all_aliases_for_note(stem: str) -> list:
    """Return the aliases list for a note stem, or [stem] if not indexed."""
    return list(state.ALIASES.get(stem, {}).get("aliases", [stem]))
