"""
Entry point: python -m keywords

Scans ./notes/ and writes a keyword frequency report to ./output/keyword report.txt.
"""
from pathlib import Path

from .extractor import extract_keywords

NOTES_DIR  = "./notes"
OUTPUT_DIR = Path("./output")
REPORT_FILE = OUTPUT_DIR / "keyword report.txt"


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Extracting keywords from notes...")
    keywords = extract_keywords(NOTES_DIR)

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("Top 20 Trigrams (Three Word Phrases):\n")
        f.write("=====================================\n\n")
        for phrase, count in keywords["trigrams"]:
            f.write(f"{phrase} ---- {count}\n")

        f.write("\nTop 20 Bigrams (Two Word Phrases):\n")
        f.write("==================================\n\n")
        for phrase, count in keywords["bigrams"]:
            f.write(f"{phrase} ---- {count}\n")

        f.write("\nTop 20 Unigrams (Single Words):\n")
        f.write("==============================\n\n")
        for word, count in keywords["unigrams"]:
            f.write(f"{word} ---- {count}\n")

    print(f"Keywords extracted successfully -> {REPORT_FILE}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        input("Press Enter to exit...")
