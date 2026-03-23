import os
import re
from pathlib import Path

import markdown
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tag import pos_tag
from nltk.tokenize import word_tokenize

# Download required NLTK data (silent if already present)
nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)
nltk.download("averaged_perceptron_tagger", quiet=True)
nltk.download("averaged_perceptron_tagger_eng", quiet=True)
nltk.download("wordnet", quiet=True)
nltk.download("stopwords", quiet=True)

_stop_words = set(stopwords.words("english"))

_SYMBOLS = {
    "", ".", ":", "'s", "(", ")", "", "[", "]", None,
    "'", ",", "`", "--", "|", ";", "?", "%", "!", " ", "*",
}


def _is_valid_word(word: str) -> bool:
    if len(word) < 3:
        return False
    if any(c in word for c in "₁₂₃₄₅₆₇₈₉₀¹²³⁴⁵⁶⁷⁸⁹⁰"):
        return False
    if not any(c.isalpha() for c in word):
        return False
    if sum(not c.isalnum() for c in word) > 1:
        return False
    return True


def _has_unique_tokens(ngram: str) -> bool:
    tokens = ngram.split()
    return len(tokens) == len(set(tokens))


def _generate_ngrams(tokens: list, n: int) -> list:
    ngrams = []
    for i in range(len(tokens) - n + 1):
        ngram = " ".join(tokens[i : i + n])
        if all(_is_valid_word(t) for t in tokens[i : i + n]):
            ngrams.append(ngram)
    return ngrams


def _get_top_ngrams(tokens: list, n: int, count: int = 20) -> tuple:
    """Return (top_ngrams, remaining_tokens) after removing tokens used in top ngrams."""
    ngram_counts: dict = {}
    for ngram in _generate_ngrams(tokens, n):
        ngram_counts[ngram] = ngram_counts.get(ngram, 0) + 1

    top = sorted(ngram_counts.items(), key=lambda x: x[1], reverse=True)[:count]
    used_tokens = {t for ngram, _ in top for t in ngram.split()}
    remaining = [t for t in tokens if t not in used_tokens]
    return top, remaining


def extract_keywords(notes_dir: str = "./notes", top_n: int = 20) -> dict:
    """
    Process all .md files in notes_dir and extract the top N trigrams, bigrams,
    and unigrams by frequency.

    Returns:
        {
            "trigrams": [(phrase, count), ...],
            "bigrams":  [(phrase, count), ...],
            "unigrams": [(word, count), ...],
        }
    """
    lemmatizer = WordNetLemmatizer()
    all_tokens: list = []

    files = [f for f in os.listdir(notes_dir) if f.endswith(".md")]
    if not files:
        print("Warning: no markdown files found in directory")
        return {"trigrams": [], "bigrams": [], "unigrams": []}

    for filename in files:
        path = os.path.join(notes_dir, filename)
        file_title = Path(filename).stem.lower()
        filename_tokens = set(file_title.split())

        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except (UnicodeDecodeError, OSError):
            continue

        # Strip code, math, wikilinks, HTML
        content = re.sub(r"```[\s\S]*?```", "", content)
        content = re.sub(r"\${1,2}[^$]*\${1,2}", "", content)
        content = re.sub(r"\[[^\]]*\]", "", content)
        content = re.sub(r"e\.g\.|i\.e\.", "", content)
        html = markdown.markdown(content)
        text = re.sub(r"<[^>]*>", "", html)
        text = re.sub(r"\w+:", "", text)
        text = re.sub(r"example", "", text)

        tokens = word_tokenize(text.lower())
        tagged = pos_tag(tokens)

        for token, tag in tagged:
            if (
                tag == "NN"
                and token not in _stop_words
                and token not in _SYMBOLS
                and _is_valid_word(token)
                and token not in filename_tokens
            ):
                all_tokens.append(lemmatizer.lemmatize(token))

    trigrams, after_trigrams = _get_top_ngrams(all_tokens, 3, top_n)
    trigrams = [(g, c) for g, c in trigrams if _has_unique_tokens(g)]

    bigrams, after_bigrams = _get_top_ngrams(after_trigrams, 2, top_n)
    bigrams = [(g, c) for g, c in bigrams if _has_unique_tokens(g)]

    unigram_freq = nltk.FreqDist(after_bigrams)
    unigrams = unigram_freq.most_common(top_n)

    return {"trigrams": trigrams, "bigrams": bigrams, "unigrams": unigrams}
