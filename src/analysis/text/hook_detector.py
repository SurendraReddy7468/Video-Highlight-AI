import re

# ── Patterns that CREATE curiosity (open loops) ──────────────
# These are GOOD for intros — they make viewer want to watch more
OPEN_LOOP_PATTERNS = [
    # Questions that don't get answered immediately
    (r"\b(have you ever|did you know|do you know why|can you guess)\b", 1.5),
    (r"\b(what if i told you|what if you could|imagine if)\b", 1.5),
    (r"\b(the reason (is|why)|here'?s why|this is why)\b", 1.3),
    (r"\b(most people don'?t|nobody tells you|they never tell)\b", 1.4),
    (r"\b(the problem is|the issue is|here'?s the thing)\b", 1.2),
    (r"\b(i (was|got|found|realized|discovered)|changed my)\b", 1.2),
    (r"\?", 1.0),   # any question mark
]

# ── Patterns that CLOSE loops (give answers) ─────────────────
# These are BAD for intros — viewer gets the answer and leaves
ANSWER_PATTERNS = [
    (r"\b(the answer is|the solution is|here'?s how|this is how)\b", -1.5),
    (r"\b(step (one|two|three|1|2|3|four|five|4|5))\b", -1.2),
    (r"\b(so basically|in conclusion|to summarize|the point is)\b", -1.0),
    (r"\b(that'?s why|which means|therefore|so what you do is)\b", -0.8),
    (r"\b(you need to|you should|you must|you have to) .{5,30}\b", -0.6),
]

# ── Patterns that signal EMOTIONAL PEAK (good for excitement) ─
EXCITEMENT_PATTERNS = [
    (r"\b(insane|crazy|unbelievable|shocking|surprising|wild)\b", 1.0),
    (r"\b(never (again|ever|thought)|completely|totally|absolutely)\b", 0.8),
    (r"\b(disappear|transform|destroy|crush|dominate|unlock)\b", 0.9),
    (r"!", 0.4),   # exclamation — capped below
]

# ── Patterns that signal PROBLEM/PAIN (relatable = watch more) ─
PAIN_PATTERNS = [
    (r"\b(wasting|losing|failing|struggling|stuck|confused|lost)\b", 1.0),
    (r"\b(stop .{1,20}ing|quit .{1,20}ing|don'?t .{1,20})\b", 0.8),
    (r"\b(everyone around you|people like you|most of us)\b", 0.9),
    (r"\b(used to|i was|i felt|i thought|before i)\b", 0.7),
]


def compute_hook_score(text: str) -> float:
    """
    Score how well a segment works as an INTRO hook.

    Key insight: a good intro hook OPENS a loop (creates curiosity)
    rather than CLOSES it (gives the answer). Segments that ask
    questions, identify problems, or tease insights score HIGH.
    Segments that give solutions, steps, or conclusions score LOW.

    Returns 0.0–1.0
      > 0.6  → strong intro hook (question/problem/tease)
      ~ 0.5  → neutral
      < 0.4  → answer/solution segment (bad for intro)
    """
    if not text:
        return 0.0

    lower = text.lower()
    score = 0.5   # start neutral

    # Open loop patterns — boost score
    for pattern, weight in OPEN_LOOP_PATTERNS:
        matches = re.findall(pattern, lower)
        score  += len(matches) * weight * 0.12

    # Answer patterns — penalize score
    for pattern, weight in ANSWER_PATTERNS:
        (r"\b(that'?s why you|which means you|so you need to|you need to stop)\b", -1.2),
        matches = re.findall(pattern, lower)
        score  += len(matches) * weight * 0.12   # weight is negative

    # Excitement patterns — mild boost
    for pattern, weight in EXCITEMENT_PATTERNS:
        matches = re.findall(pattern, lower)
        if pattern == "!":
            score += min(len(matches) * 0.05, 0.15)
        else:
            score += len(matches) * weight * 0.08

    # Pain/relatable patterns — boost
    for pattern, weight in PAIN_PATTERNS:
        (r"\b(poisoned|toxic|killing|destroying|sabotaging)\b", 1.2),
        matches = re.findall(pattern, lower)
        score  += len(matches) * weight * 0.10

    # Punchy short sentences — good for hooks
    sentences = [s.strip() for s in re.split(r'[.!?]', text) if s.strip()]
    punchy    = sum(1 for s in sentences if 3 <= len(s.split()) <= 12)
    if sentences:
        score += (punchy / len(sentences)) * 0.15

    return round(max(0.0, min(1.0, score)), 4)


if __name__ == "__main__":
    tests = [
        # Should score HIGH (open loops, problems, questions)
        "Have you ever wondered why you keep failing even when you work hard?",
        "Most people around you are poisoned to your growth and you don't even know it.",
        "I used to waste 4 hours every single day and I had no idea.",
        "Did you know that 99% of people never achieve their goals? Here's why.",

        # Should score LOW (gives answers, closes loops)
        "Step one is to wake up early and plan your day the night before.",
        "So basically the solution is to focus on one thing at a time.",
        "That's why you need to stop wasting time and start working harder.",
        "In conclusion, the five step framework will change your life.",
    ]
    print("OPEN LOOP (should be HIGH > 0.6):")
    for t in tests[:4]:
        print(f"  {compute_hook_score(t):.2f}  {t[:65]}")
    print("\nCLOSED LOOP (should be LOW < 0.5):")
    for t in tests[4:]:
        print(f"  {compute_hook_score(t):.2f}  {t[:65]}")