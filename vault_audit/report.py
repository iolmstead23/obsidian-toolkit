from datetime import datetime

from . import state
from .constants import REPORT_FILE, SIMILARITY_THRESHOLD
from .filenames import collect_filename_issues
from .io import get_all_notes
from .unlinked import _build_search_forms, find_unlinked_references
from .utils import clear_screen


def _format_aliases_table() -> list:
    lines = ["| Note | Aliases |", "|---|---|"]
    for stem in sorted(state.ALIASES.keys()):
        aliases = state.ALIASES[stem].get("aliases", [])
        lines.append(f"| `{stem}` | {', '.join(f'`{a}`' for a in aliases)} |")
    return lines


def run_generate_report() -> None:
    """Menu Option 4: generate a combined audit report at output/vault_report.md."""
    clear_screen()
    print("\n── Option 4: Generate Report ─────────────────────────────────────────")
    notes = get_all_notes()
    REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Obsidian Vault Audit Report",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  ",
        f"Notes scanned: {len(notes)}",
        "",
    ]

    # Filename Violations
    lines += ["---", "", "## Filename Violations", ""]
    renames, acronyms, corrupted = collect_filename_issues(notes)

    if corrupted:
        lines += ["### Corrupted Files", ""]
        for path, reason in corrupted:
            lines.append(f"- `{path.name}` — {reason}")
        lines.append("")

    if acronyms:
        lines += ["### Acronym Filenames (Manual Review Required)", ""]
        for path in acronyms:
            lines.append(f"- `{path.name}`")
        lines.append("")

    if renames:
        lines += ["### Proposed Renames", ""]
        lines += ["| Current Filename | Proposed Filename |", "|---|---|"]
        for path, proposed in renames:
            note = " *(possible duplicate)*" if "(1)" in path.stem else ""
            lines.append(f"| `{path.name}` | `{proposed}.md`{note} |")
        lines.append("")
    elif not corrupted and not acronyms:
        lines += ["*No filename violations detected.*", ""]

    # Duplicate Pairs
    lines += ["---", "", "## Duplicate Pairs", ""]
    if state._cached_pairs is None:
        lines += ["*No similarity analysis available — run Option 2 first.*", ""]
    elif not state._cached_pairs:
        lines += [f"*No duplicate pairs found above threshold {SIMILARITY_THRESHOLD}.*", ""]
    else:
        lines += [
            f"Similarity threshold: **{SIMILARITY_THRESHOLD}**  ",
            f"{len(state._cached_pairs)} pair(s) detected.",
            "",
            "| Note A | Note B | Score |",
            "|---|---|---|",
        ]
        for stem_a, stem_b, score in state._cached_pairs:
            lines.append(f"| `{stem_a}.md` | `{stem_b}.md` | {score:.3f} |")
        lines.append("")

    # Unlinked References
    lines += ["---", "", "## Potential Unlinked References", ""]
    if not state.ALIASES:
        lines += ["*Alias map is empty — run Option 5 (Build Alias Map) first.*", ""]
    else:
        forms = _build_search_forms(notes)
        unlinked_by_note: dict = {}
        for note_path in notes:
            matches = find_unlinked_references(note_path, forms)
            if matches:
                unlinked_by_note[note_path.stem] = matches

        if not unlinked_by_note:
            lines += ["*No unlinked references detected.*", ""]
        else:
            total = sum(len(v) for v in unlinked_by_note.values())
            lines += [f"{total} potential link(s) across {len(unlinked_by_note)} note(s).", ""]
            for stem in sorted(unlinked_by_note.keys()):
                matches = unlinked_by_note[stem]
                lines.append(f"**{stem}.md** ({len(matches)} match(es))")
                for surface, canonical, _ in matches[:5]:
                    lines.append(f"  - `{surface}` → `[[{canonical}]]`")
                if len(matches) > 5:
                    lines.append(f"  - *(and {len(matches) - 5} more...)*")
                lines.append("")

    # Alias Map
    lines += ["---", "", "## Alias Map", ""]
    if not state.ALIASES:
        lines += ["*No aliases indexed. Run Option 5 to build the alias map.*", ""]
    else:
        lines += _format_aliases_table()
        lines.append("")

    REPORT_FILE.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n  Report written to {REPORT_FILE}")
    input("\nPress Enter to return to menu...")
