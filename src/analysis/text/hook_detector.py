import re

# Patterns that signal a strong hook moment
QUESTION_PATTERNS = [
    r"\?",                          # any question
    r"\b(what if|imagine|think about|have you ever|did you know)\b",
    r"\b(how many|how much|how long|how often)\b",
]

CLAIM_PATTERNS = [
    r"\b(never|always|every single|no one|everyone|nobody|everybody)\b",
    r"\b(the truth is|the reality is|fact is|honest(ly)?|real talk)\b",
    r"\b(most people|99%|majority|almost everyone)\b",
    r"\b(change(d)? my life|life-changing|blew my mind|mind-blowing)\b",
]

CONTRAST_PATTERNS = [
    r"\b(but here'?s the thing|the problem is|the issue is|however)\b",
    r"\b(instead of|rather than|not .{1,20} but)\b",
    r"\b(stop .{1,20}ing|don'?t .{1,20}|quit .{1,20}ing)\b",
]

URGENCY_PATTERNS = [
    r"\b(right now|immediately|today|this moment|wake up)\b",
    r"\b(before it'?s too late|running out of|you need to|you must)\b",
    r"\b(warning|danger|urgent|critical|important)\b",
]

ALL_PATTERNS = (
    [(p, 1.0) for p in QUESTION_PATTERNS] +
    [(p, 1.2) for p in CLAIM_PATTERNS] +
    [(p, 1.0) for p in CONTRAST_PATTERNS] +
    [(p, 0.8) for p in URGENCY_PATTERNS]
)


def compute_hook_score(text: str) -> float:
    """
    Detect how 'hook-worthy' a segment is — bold claims, questions,
    contrast moments, and urgency language all score higher.

    Returns 0.0–1.0. Scores above 0.5 are strong hook candidates.

    Why hooks matter: The first 3 seconds of a Short/Reel determine
    if someone keeps watching. A hook segment grabs attention
    immediately — it makes the viewer ask "wait, what?"
    """
    if not text:
        return 0.0

    lower  = text.lower()
    score  = 0.0

    for pattern, weight in ALL_PATTERNS:
        matches = re.findall(pattern, lower)
        score  += len(matches) * weight * 0.15

    # Bonus: short punchy sentences score higher (under 10 words = punchy)
    sentences = [s.strip() for s in re.split(r'[.!?]', text) if s.strip()]
    punchy    = sum(1 for s in sentences if len(s.split()) <= 10)
    if sentences:
        score += (punchy / len(sentences)) * 0.2

    # Bonus: exclamation marks signal emphasis
    score += min(text.count('!') * 0.1, 0.2)

    return round(min(score, 1.0), 4)


if __name__ == "__main__":
    tests = [
        "Most people will never achieve their goals because they quit too early.",
        "And then what happened was we went to the store.",
        "Have you ever wondered why successful people think differently?",
        "Stop making excuses. Right now. Today is the day you change.",
        "The algorithm basically processes input data through layers.",
    ]
    for t in tests:
        print(f"{compute_hook_score(t):.2f}  |  {t[:65]}")