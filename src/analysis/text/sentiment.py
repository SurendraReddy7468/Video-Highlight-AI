import re


# Positive and negative word lists for lightweight sentiment scoring.
# No external ML model needed — fast and works offline.
POSITIVE_WORDS = {
    "amazing","awesome","brilliant","excellent","fantastic","good","great",
    "happy","incredible","inspiring","love","outstanding","perfect","positive",
    "powerful","remarkable","success","superb","wonderful","best","better",
    "important","key","critical","essential","significant","valuable","unique",
    "innovative","effective","proven","clear","strong","smart","fast","easy",
    "excited","exciting","opportunity","growth","win","top","leading","major",
}

NEGATIVE_WORDS = {
    "bad","boring","confusing","dangerous","difficult","disappointing","fail",
    "failure","hard","horrible","impossible","misleading","mistake","never",
    "no","nothing","problem","terrible","useless","waste","weak","worst",
    "wrong","avoid","beware","concern","critical","fear","loss","poor","risk",
    "struggle","unfortunately","unlikely","unclear","limited","broken","dead",
}


def compute_sentiment_score(text: str) -> float:
    """
    Score text sentiment on a scale from 0.0 (very negative) to 1.0 (very positive).
    Neutral text scores around 0.5.

    Why sentiment matters: Highly positive or emotionally charged moments
    tend to be the most shareable/engaging parts of a podcast.
    Both strong positive AND strong negative moments score high —
    extremes are more interesting than neutral filler.

    Returns:
        float between 0.0 and 1.0
          > 0.6  → positive / emotional moment  (good highlight)
          ~ 0.5  → neutral
          < 0.4  → negative / critical moment   (also good highlight)
    """
    words = re.findall(r"[a-z]+", text.lower())
    if not words:
        return 0.5   # neutral default

    pos_count = sum(1 for w in words if w in POSITIVE_WORDS)
    neg_count = sum(1 for w in words if w in NEGATIVE_WORDS)
    total     = len(words)

    pos_ratio = pos_count / total
    neg_ratio = neg_count / total

    # Raw sentiment: +1 = fully positive, -1 = fully negative
    raw = pos_ratio - neg_ratio

    # Normalize to 0.0–1.0 range centered at 0.5
    # Clamp raw to [-0.3, 0.3] — typical speech rarely exceeds this
    normalized = (raw + 0.3) / 0.6
    normalized = max(0.0, min(1.0, normalized))

    # Boost score for emotional intensity (either direction = more engaging)
    intensity  = (pos_ratio + neg_ratio) / 0.3   # how emotional overall
    intensity  = min(intensity, 1.0)
    final      = 0.5 + (normalized - 0.5) * (0.5 + 0.5 * intensity)

    return round(max(0.0, min(1.0, final)), 4)


if __name__ == "__main__":
    tests = [
        "This is an amazing and powerful technique that leads to incredible results",
        "The problem is completely broken and this approach is a terrible mistake",
        "So basically what we are talking about is the general idea of the concept",
    ]
    for t in tests:
        print(f"{compute_sentiment_score(t):.2f}  |  {t[:60]}")