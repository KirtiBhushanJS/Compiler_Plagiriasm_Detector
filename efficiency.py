"""Utility module for assessing code efficiency and energy consumption.

Provides a simple static analysis that works for both Python and C source code.
The analysis is lightweight and does **not** require external dependencies.
It extracts basic metrics such as:
- Lines of code (excluding blanks and comments)
- Number of functions / methods
- Number of loop constructs (`for`, `while` in Python; `for`, `while`, `do` in C)
- Approximate cyclomatic complexity (very rough estimate based on decision points)
- Estimated energy consumption proxy (derived from metric weights)

The results are returned as a dictionary that can be displayed in the Rich report.
"""
import re
from typing import Dict, List

# Helper regex patterns for C and Python
_C_COMMENT_PATTERN = re.compile(r"/\*.*?\*/", re.DOTALL)
_C_LINE_COMMENT_PATTERN = re.compile(r"//.*?$", re.MULTILINE)
_PY_COMMENT_PATTERN = re.compile(r"#.*?$", re.MULTILINE)

def _strip_comments(code: str, language: str) -> str:
    """Remove comments from source code for more accurate metric calculation.

    Args:
        code: Raw source code as a string.
        language: "C" or "Python" (case‑insensitive).
    """
    if language.lower() == "c":
        # Remove block comments first, then line comments
        code = _C_COMMENT_PATTERN.sub("", code)
        code = _C_LINE_COMMENT_PATTERN.sub("", code)
    else:
        # Python only has line comments ("#")
        code = _PY_COMMENT_PATTERN.sub("", code)
    return code

def _count_functions(code: str, language: str) -> int:
    """Count function / method definitions.

    For C we look for a pattern like ``return_type name(...){``.
    For Python we count lines starting with ``def `` (ignoring indentation).
    """
    if language.lower() == "c":
        # Very permissive C function pattern
        pattern = re.compile(r"^[\w\*\s]+\s+\w+\s*\([^;]*\)\s*\{", re.MULTILINE)
    else:
        pattern = re.compile(r"^\s*def\s+\w+\s*\(")
    return len(pattern.findall(code))

def _count_loops(code: str, language: str) -> int:
    """Count loop constructs.

    C: ``for``, ``while``, ``do``.
    Python: ``for``, ``while``.
    """
    if language.lower() == "c":
        loops = re.findall(r"\b(for|while|do)\b", code)
    else:
        loops = re.findall(r"\b(for|while)\b", code)
    return len(loops)

def _count_decisions(code: str, language: str) -> int:
    """Count decision points used for a rough cyclomatic complexity estimate.

    Includes ``if``, ``elif``/``else if``, ``switch`` (C), ``case`` (C), and ternary ``?`` (C).
    Python's ``elif`` is counted as a separate ``if``.
    """
    if language.lower() == "c":
        decisions = re.findall(r"\b(if|else\s+if|switch|case|\?)\b", code)
    else:
        decisions = re.findall(r"\b(if|elif)\b", code)
    return len(decisions)

def analyze_efficiency(code: str, language: str) -> Dict[str, int]:
    """Perform a lightweight static analysis and return efficiency metrics.

    The **energy consumption proxy** is a simple weighted sum:
        energy = 0.5 * LOC + 1.0 * loops + 1.5 * decisions
    where LOC is lines of code (excluding blanks and comments).
    The weight values are illustrative – they give a higher cost to control‑flow
    structures which tend to increase runtime and CPU usage.
    """
    # Normalise language string
    lang = language.strip().lower()
    # Strip comments and split into lines
    code_nocomments = _strip_comments(code, lang)
    lines = [ln for ln in code_nocomments.splitlines() if ln.strip()]
    loc = len(lines)
    functions = _count_functions(code_nocomments, lang)
    loops = _count_loops(code_nocomments, lang)
    decisions = _count_decisions(code_nocomments, lang)
    # Rough cyclomatic complexity (CC) = decisions + 1
    cyclomatic_complexity = decisions + 1
    # Energy proxy (arbitrary units)
    energy = int(0.5 * loc + 1.0 * loops + 1.5 * decisions)
    return {
        "Lines of Code": loc,
        "Functions": functions,
        "Loops": loops,
        "Decision Points": decisions,
        "Cyclomatic Complexity": cyclomatic_complexity,
        "Energy Estimate": energy,
    }

__all__ = ["analyze_efficiency"]

