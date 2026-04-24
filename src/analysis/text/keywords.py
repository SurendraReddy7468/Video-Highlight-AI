import re
from collections import Counter


# Common English stop words to ignore
STOP_WORDS = {
    "a","an","the","and","or","but","in","on","at","to","for","of","with",
    "is","it","its","was","are","be","been","being","have","has","had",
    "do","does","did","will","would","could","should","may","might","shall",
    "this","that","these","those","i","you","he","she","we","they","me",
    "him","her","us","them","my","your","his","our","their","what","which",
    "who","how","when","where","why","all","any","both","each","so","if",
    "not","no","as","by","from","up","about","into","then","than","just",
    "also","very","more","most","some","such","there","their","can","get",
}


def compute_keyword_score(text: str, corpus_segments: list = None) -> float:
    """
    Score a text segment by keyword density — how many meaningful,
    non-trivial words it contains relative to its total word count.

    Returns a score between 0.0 and 1.0.

    Why keywords matter: Segments packed with domain-specific or
    meaningful words are more likely to be informative highlights
    compared to filler ("um", "you know", "so basically").

    Args:
        text:             The segment text to score
        corpus_segments:  Optional list of all segment texts — if provided,
                          rare words score higher (TF-IDF style boost)
    """
    words = re.findall(r"[a-z]+", text.lower())
    if not words:
        return 0.0

    # Filter out stop words and very short words
    content_words = [w for w in words if w not in STOP_WORDS and len(w) > 3]

    # Base score: ratio of content words to total words
    base_score = len(content_words) / len(words)

    # Optional: boost words that appear rarely across all segments (more unique = more valuable)
    if corpus_segments and len(corpus_segments) > 1:
        all_text   = " ".join(corpus_segments).lower()
        all_words  = re.findall(r"[a-z]+", all_text)
        word_freq  = Counter(all_words)
        total_docs = len(corpus_segments)

        # Count how many segments each word appears in
        seg_counts = Counter()
        for seg in corpus_segments:
            unique_in_seg = set(re.findall(r"[a-z]+", seg.lower()))
            seg_counts.update(unique_in_seg)

        # IDF boost: penalize common words, reward rare ones
        import math
        idf_scores = []
        for w in content_words:
            df = seg_counts.get(w, 1)
            idf = math.log(total_docs / df + 1)
            idf_scores.append(idf)

        if idf_scores:
            avg_idf      = sum(idf_scores) / len(idf_scores)
            max_possible = math.log(total_docs + 1)
            idf_boost    = min(avg_idf / max_possible, 1.0) if max_possible > 0 else 0.0
            # Blend base score and IDF boost
            base_score = 0.6 * base_score + 0.4 * idf_boost

    return round(min(base_score, 1.0), 4)


if __name__ == "__main__":
    sample = "Artificial intelligence is a broad branch of computer science focused on building smart machines"
    print(f"Keyword score: {compute_keyword_score(sample)}")