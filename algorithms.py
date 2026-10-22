"""algorithms.py
Multiple similarity algorithms for structural plagiarism detection.

Provides:
- Jaccard Similarity (set-based structural token overlap)
- Cosine Similarity (frequency-vector based)
- LCS Ratio (Longest Common Subsequence ratio)
- Combined weighted score
"""
import re
import math
from collections import Counter
from typing import List, Tuple


# ---------------------------------------------------------------------------
# Token Extraction
# ---------------------------------------------------------------------------

def tokenize(code: str) -> List[str]:
    """Extract meaningful tokens from source code, normalizing identifiers."""
    # Normalize string literals
    code = re.sub(r'".*?"', '"STR"', code)
    code = re.sub(r"'.*?'", "'STR'", code)
    # Normalize numbers
    code = re.sub(r'\b\d+(\.\d+)?\b', 'NUM', code)
    # Extract tokens (words and operators)
    tokens = re.findall(r'[a-zA-Z_]\w*|[+\-*/=<>!&|^~%]+|[(){}\[\];,.]', code)
    return tokens


# ---------------------------------------------------------------------------
# Algorithm 1: Jaccard Similarity
# ---------------------------------------------------------------------------

def jaccard_similarity(seq1: List[str], seq2: List[str]) -> float:
    """Compute Jaccard similarity between two token sequences using n-grams (n=3)."""
    def ngrams(seq, n=3):
        return set(tuple(seq[i:i+n]) for i in range(len(seq) - n + 1))

    if not seq1 or not seq2:
        return 0.0

    set1 = ngrams(seq1)
    set2 = ngrams(seq2)

    if not set1 and not set2:
        return 100.0

    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return round((intersection / union) * 100, 2) if union > 0 else 0.0


# ---------------------------------------------------------------------------
# Algorithm 2: Cosine Similarity
# ---------------------------------------------------------------------------

def cosine_similarity(seq1: List[str], seq2: List[str]) -> float:
    """Compute cosine similarity using term-frequency vectors over token unigrams."""
    if not seq1 or not seq2:
        return 0.0

    freq1 = Counter(seq1)
    freq2 = Counter(seq2)
    all_tokens = set(freq1) | set(freq2)

    dot_product = sum(freq1.get(t, 0) * freq2.get(t, 0) for t in all_tokens)
    mag1 = math.sqrt(sum(v ** 2 for v in freq1.values()))
    mag2 = math.sqrt(sum(v ** 2 for v in freq2.values()))

    if mag1 == 0 or mag2 == 0:
        return 0.0
    return round((dot_product / (mag1 * mag2)) * 100, 2)


# ---------------------------------------------------------------------------
# Algorithm 3: LCS Ratio
# ---------------------------------------------------------------------------

def lcs_ratio(seq1: List[str], seq2: List[str]) -> float:
    """Compute the Longest Common Subsequence ratio between two token sequences.

    Uses a space-optimised DP approach (two-row DP) to avoid O(n*m) memory.
    """
    if not seq1 or not seq2:
        return 0.0

    # Cap length for performance
    s1 = seq1[:300]
    s2 = seq2[:300]
    m, n = len(s1), len(s2)

    prev = [0] * (n + 1)
    for i in range(1, m + 1):
        curr = [0] * (n + 1)
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                curr[j] = prev[j - 1] + 1
            else:
                curr[j] = max(prev[j], curr[j - 1])
        prev = curr

    lcs_len = prev[n]
    ratio = (2 * lcs_len) / (m + n) if (m + n) > 0 else 0.0
    return round(ratio * 100, 2)


# ---------------------------------------------------------------------------
# Combined Score
# ---------------------------------------------------------------------------

def combined_score(seq1: List[str], seq2: List[str]) -> Tuple[float, float, float, float]:
    """Return (jaccard, cosine, lcs, combined_weighted) scores in [0, 100]."""
    j = jaccard_similarity(seq1, seq2)
    c = cosine_similarity(seq1, seq2)
    l = lcs_ratio(seq1, seq2)
    # Weighted: LCS has highest structural weight
    combined = round(0.35 * j + 0.30 * c + 0.35 * l, 2)
    return j, c, l, combined


__all__ = ["tokenize", "jaccard_similarity", "cosine_similarity", "lcs_ratio", "combined_score"]
