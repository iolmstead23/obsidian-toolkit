import shutil
from datetime import datetime
from pathlib import Path

from . import state
from .aliases import get_all_aliases_for_note, save_aliases
from .constants import DUPLICATES_DIR, MODEL_NAME, SIMILARITY_THRESHOLD
from .filenames import update_wikilinks_for_rename
from .io import get_all_notes, read_note, strip_markdown_for_text
from .utils import clear_screen


def _load_sentence_transformer():
    """Lazy-load and cache the SentenceTransformer model. Returns None on failure."""
    if state._model is not None:
        return state._model
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
        print(f"  Loading model '{MODEL_NAME}' (first run downloads ~80 MB)...")
        state._model = SentenceTransformer(MODEL_NAME)
        print("  Model ready.")
        return state._model
    except ImportError:
        print("  [!] sentence-transformers is not installed.")
        print("      Run: pip install sentence-transformers")
        return None
    except Exception as e:
        print(f"  [!] Model load failed: {e}")
        return None


def _compute_embeddings(note_texts: dict) -> tuple:
    """Given {stem: plain_text}, return (matrix_ndarray, stems_list)."""
    model = _load_sentence_transformer()
    if model is None:
        return None, []
    stems = list(note_texts.keys())
    texts = [note_texts[s] for s in stems]
    print(f"  Encoding {len(texts)} notes...")
    matrix = model.encode(texts, batch_size=32, show_progress_bar=True)
    return matrix, stems


def _find_duplicate_pairs(matrix, stems: list, threshold: float = SIMILARITY_THRESHOLD) -> list:
    """
    Return (stem_a, stem_b, score) tuples where cosine similarity >= threshold.
    Upper triangle only, sorted by score descending.
    """
    from sklearn.metrics.pairwise import cosine_similarity  # type: ignore
    sim = cosine_similarity(matrix)
    pairs = []
    n = len(stems)
    for i in range(n):
        for j in range(i + 1, n):
            score = float(sim[i, j])
            if score >= threshold:
                pairs.append((stems[i], stems[j], score))
    pairs.sort(key=lambda x: x[2], reverse=True)
    return pairs


def _archive_note(path: Path) -> Path:
    """Move path to DUPLICATES_DIR. Appends timestamp if destination exists."""
    DUPLICATES_DIR.mkdir(parents=True, exist_ok=True)
    dest = DUPLICATES_DIR / path.name
    if dest.exists():
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = DUPLICATES_DIR / f"{path.stem}_{ts}{path.suffix}"
    shutil.move(str(path), str(dest))
    return dest


def run_duplicate_detection() -> None:
    """Menu Option 2: compute semantic similarity and handle duplicate note pairs."""
    clear_screen()
    print("\n── Option 2: Duplicate Detection ────────────────────────────────────")
    notes = get_all_notes()
    if not notes:
        print("  No notes found.")
        input("\nPress Enter to return to menu...")
        return

    note_texts = {}
    for p in notes:
        raw = read_note(p)
        if raw is not None:
            note_texts[p.stem] = strip_markdown_for_text(raw)

    matrix, stems = _compute_embeddings(note_texts)
    if matrix is None:
        input("\nPress Enter to return to menu...")
        return

    pairs = _find_duplicate_pairs(matrix, stems)
    state._cached_pairs = pairs

    if not pairs:
        print(f"\n  No pairs found above similarity threshold {SIMILARITY_THRESHOLD}.")
        input("\nPress Enter to return to menu...")
        return

    print(f"\n  {len(pairs)} pair(s) at or above threshold {SIMILARITY_THRESHOLD}:\n")
    stem_to_path = {p.stem: p for p in notes}
    total = len(pairs)

    for idx, (stem_a, stem_b, score) in enumerate(pairs, 1):
        path_a = stem_to_path.get(stem_a)
        path_b = stem_to_path.get(stem_b)
        if path_a is None or not path_a.exists():
            continue
        if path_b is None or not path_b.exists():
            continue

        size_a = path_a.stat().st_size / 1024
        size_b = path_b.stat().st_size / 1024
        preview_a = note_texts.get(stem_a, "")[:200].replace("\n", " ")
        preview_b = note_texts.get(stem_b, "")[:200].replace("\n", " ")

        print(f"  Pair {idx}/{total}  |  Score: {score:.3f}")
        print(f"    A: {stem_a}.md  ({size_a:.1f} KB)")
        print(f"       {preview_a}")
        print(f"    B: {stem_b}.md  ({size_b:.1f} KB)")
        print(f"       {preview_b}\n")

        while True:
            print("  Keep: [A] / [B] / [s]kip / [q]uit to menu: ", end="")
            c = input().strip().lower()
            if c in ("a", "b", "s", "q"):
                break
            print("  Please enter A, B, s, or q.")

        if c == "q":
            break
        if c == "s":
            print("  Skipped.\n")
            continue

        kept      = stem_a if c == "a" else stem_b
        discarded = stem_b if c == "a" else stem_a
        discard_path = stem_to_path[discarded]

        dest = _archive_note(discard_path)
        fresh = get_all_notes()
        n = update_wikilinks_for_rename(discarded, kept, fresh)

        disc_aliases = get_all_aliases_for_note(discarded)
        kept_entry = state.ALIASES.setdefault(kept, {"aliases": [kept]})
        for a in disc_aliases:
            if a not in kept_entry["aliases"]:
                kept_entry["aliases"].append(a)
        state.ALIASES.pop(discarded, None)
        save_aliases()

        print(f"  Archived: {discard_path.name}  ->  _duplicates/{dest.name}")
        print(f"  Wikilinks updated in {n} file(s).\n")

    input("\nPress Enter to return to menu...")
