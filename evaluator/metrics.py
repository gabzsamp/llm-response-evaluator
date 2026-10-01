"""Pure functions for scoring, consistency checks and inter-annotator agreement.

No input/output happens here, which keeps these functions easy to unit test.
"""
from collections import Counter

DIMENSIONS = ("accuracy", "instruction_following", "clarity")
MIN_SCORE, MAX_SCORE = 1, 5
CHOICES = ("A", "B", "tie")
MIN_JUSTIFICATION_WORDS = 8


def validate_scores(scores):
    """Raise ValueError unless every dimension has an integer score from 1 to 5."""
    for dim in DIMENSIONS:
        if dim not in scores:
            raise ValueError(f"missing score for '{dim}'")
        value = scores[dim]
        if not isinstance(value, int) or not MIN_SCORE <= value <= MAX_SCORE:
            raise ValueError(f"'{dim}' must be an integer from {MIN_SCORE} to {MAX_SCORE}")


def total_score(scores):
    """Sum of all rubric dimensions for one response."""
    validate_scores(scores)
    return sum(scores[dim] for dim in DIMENSIONS)


def implied_preference(scores_a, scores_b):
    """Which response the rubric scores favour: 'A', 'B' or 'tie'."""
    total_a, total_b = total_score(scores_a), total_score(scores_b)
    if total_a > total_b:
        return "A"
    if total_b > total_a:
        return "B"
    return "tie"


def qa_findings(record):
    """Return a list of problems found in one evaluation record (empty list = OK).

    Flags:
      * the preferred answer contradicts the rubric scores
      * the justification is too short to be useful
    """
    findings = []
    implied = implied_preference(record["scores_a"], record["scores_b"])
    preferred = record["preferred"]
    if preferred not in CHOICES:
        findings.append(f"invalid choice '{preferred}'")
    elif "A" in (preferred, implied) and "B" in (preferred, implied):
        findings.append(
            f"contradiction: preferred {preferred} but rubric scores favour {implied}"
        )
    words = len(record.get("justification", "").split())
    if words < MIN_JUSTIFICATION_WORDS:
        findings.append(
            f"justification too short ({words} words, minimum {MIN_JUSTIFICATION_WORDS})"
        )
    return findings


def cohens_kappa(labels_a, labels_b):
    """Cohen's kappa between two raters who labelled the same items.

    kappa = (observed agreement - chance agreement) / (1 - chance agreement)
    1.0 = perfect agreement, 0 = no better than chance, negative = worse than chance.
    """
    if len(labels_a) != len(labels_b):
        raise ValueError("both raters must label the same number of items")
    if not labels_a:
        raise ValueError("no items to compare")
    n = len(labels_a)
    observed = sum(a == b for a, b in zip(labels_a, labels_b)) / n
    count_a, count_b = Counter(labels_a), Counter(labels_b)
    chance = sum((count_a[c] / n) * (count_b[c] / n) for c in set(count_a) | set(count_b))
    if chance == 1:  # both raters used one identical label for everything
        return 1.0
    return (observed - chance) / (1 - chance)


def interpret_kappa(kappa):
    """Plain-language label (Landis & Koch scale)."""
    if kappa < 0:
        return "worse than chance"
    for limit, label in ((0.20, "slight"), (0.40, "fair"), (0.60, "moderate"), (0.80, "substantial")):
        if kappa <= limit:
            return label
    return "almost perfect"
