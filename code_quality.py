"""code_quality.py
Advanced static code quality analysis for Python and C source code.

Provides:
- Basic metrics (LOC, functions, loops, decisions)
- Halstead complexity metrics
- Cyclomatic complexity
- Code smell detection (deep nesting, long functions, magic numbers, long lines)
- Maintainability Index (MI)
- Energy consumption estimate
- Actionable improvement suggestions
"""
import re
import math
from typing import Dict, List, Any


# ---------------------------------------------------------------------------
# Comment stripping
# ---------------------------------------------------------------------------

_C_BLOCK_COMMENT = re.compile(r'/\*.*?\*/', re.DOTALL)
_C_LINE_COMMENT = re.compile(r'//.*?$', re.MULTILINE)
_PY_COMMENT = re.compile(r'#.*?$', re.MULTILINE)
_PY_DOCSTRING = re.compile(r'(""".*?"""|\'\'\'.*?\'\'\')', re.DOTALL)


def strip_comments(code: str, language: str) -> str:
    """Remove comments and docstrings from source code."""
    lang = language.lower()
    if lang == 'c':
        code = _C_BLOCK_COMMENT.sub('', code)
        code = _C_LINE_COMMENT.sub('', code)
    else:
        code = _PY_DOCSTRING.sub('', code)
        code = _PY_COMMENT.sub('', code)
    return code


# ---------------------------------------------------------------------------
# Basic Metrics
# ---------------------------------------------------------------------------

def count_loc(code: str) -> int:
    """Count non-blank, non-comment lines."""
    return len([ln for ln in code.splitlines() if ln.strip()])


def count_functions(code: str, language: str) -> int:
    """Count function/method definitions."""
    if language.lower() == 'c':
        pat = re.compile(r'^[\w\*\s]+\s+\w+\s*\([^;]*\)\s*\{', re.MULTILINE)
    else:
        pat = re.compile(r'^\s*(?:async\s+)?def\s+\w+\s*\(', re.MULTILINE)
    return len(pat.findall(code))


def count_loops(code: str, language: str) -> int:
    """Count loop constructs."""
    if language.lower() == 'c':
        return len(re.findall(r'\b(for|while|do)\b', code))
    return len(re.findall(r'\b(for|while)\b', code))


def count_decisions(code: str, language: str) -> int:
    """Count decision/branching points."""
    if language.lower() == 'c':
        return len(re.findall(r'\b(if|else\s+if|switch|case|\?)\b', code))
    return len(re.findall(r'\b(if|elif|and\b|or\b)\b', code))


# ---------------------------------------------------------------------------
# Halstead Metrics
# ---------------------------------------------------------------------------

_C_OPERATORS = {'+', '-', '*', '/', '%', '=', '==', '!=', '<', '>', '<=', '>=',
                '&&', '||', '!', '&', '|', '^', '~', '<<', '>>', '++', '--',
                '+=', '-=', '*=', '/=', '%=', '->', '.', ',', ';'}

_PY_OPERATORS = {'+', '-', '*', '/', '//', '%', '**', '=', '==', '!=', '<', '>',
                 '<=', '>=', 'and', 'or', 'not', 'in', 'not in', 'is', 'is not',
                 '&', '|', '^', '~', '<<', '>>', '+=', '-=', '*=', '/=', ',', ':'}

_KEYWORDS_C = {'auto', 'break', 'case', 'char', 'const', 'continue', 'default',
               'do', 'double', 'else', 'enum', 'extern', 'float', 'for', 'goto',
               'if', 'int', 'long', 'register', 'return', 'short', 'signed',
               'sizeof', 'static', 'struct', 'switch', 'typedef', 'union',
               'unsigned', 'void', 'volatile', 'while'}

_KEYWORDS_PY = {'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await',
                'break', 'class', 'continue', 'def', 'del', 'elif', 'else',
                'except', 'finally', 'for', 'from', 'global', 'if', 'import',
                'in', 'is', 'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise',
                'return', 'try', 'while', 'with', 'yield'}


def halstead_metrics(code: str, language: str) -> Dict[str, Any]:
    """Compute Halstead complexity metrics."""
    lang = language.lower()
    keywords = _KEYWORDS_C if lang == 'c' else _KEYWORDS_PY

    # Tokenize
    tokens = re.findall(r'[a-zA-Z_]\w*|[+\-*/%=<>!&|^~]+|[(){}\[\];,.]', code)
    operators = []
    operands = []

    for tok in tokens:
        if tok in keywords or re.match(r'^[+\-*/%=<>!&|^~(){}\[\];,.]+$', tok):
            operators.append(tok)
        elif re.match(r'^[a-zA-Z_]\w*$', tok) or re.match(r'^\d+$', tok):
            operands.append(tok)

    # Halstead counts
    n1 = len(set(operators))   # distinct operators
    n2 = len(set(operands))    # distinct operands
    N1 = len(operators)         # total operators
    N2 = len(operands)          # total operands

    n = n1 + n2                 # vocabulary
    N = N1 + N2                 # length

    if n1 == 0 or n2 == 0:
        return {'Vocabulary': n, 'Length': N, 'Volume': 0,
                'Difficulty': 0, 'Effort': 0, 'Bugs Estimate': 0}

    volume = round(N * math.log2(n), 2) if n > 0 else 0
    difficulty = round((n1 / 2) * (N2 / n2), 2) if n2 > 0 else 0
    effort = round(difficulty * volume, 2)
    bugs = round(volume / 3000, 4)  # Halstead bug estimate

    return {
        'Vocabulary': n,
        'Length': N,
        'Volume': volume,
        'Difficulty': difficulty,
        'Effort': effort,
        'Bugs Estimate': bugs,
    }


# ---------------------------------------------------------------------------
# Code Smells
# ---------------------------------------------------------------------------

def detect_code_smells(original_code: str, clean_code: str, language: str) -> List[str]:
    """Detect common code quality issues (smells)."""
    smells = []
    lines = original_code.splitlines()
    lang = language.lower()

    # 1. Long lines (> 79 chars, PEP 8 / Linux coding style)
    long_lines = [i + 1 for i, ln in enumerate(lines) if len(ln) > 100]
    if long_lines:
        smells.append(f"Long lines (>100 chars) at lines: {', '.join(map(str, long_lines[:5]))}{'...' if len(long_lines) > 5 else ''}")

    # 2. Deep nesting (more than 3 levels of indentation)
    for i, ln in enumerate(lines):
        indent = len(ln) - len(ln.lstrip())
        if lang == 'python' and indent > 12:  # 4 spaces * 3 = 12
            smells.append(f"Deep nesting (>3 levels) detected at line {i+1}")
            break
        elif lang == 'c' and ln.count('{') + ln.count('}') == 0:
            brace_depth = 0
            for ch in ln:
                if ch == '{':
                    brace_depth += 1
            if brace_depth > 4:
                smells.append(f"Possible deep nesting detected at line {i+1}")
                break

    # 3. Magic numbers (numeric literals other than 0 and 1 outside assignments)
    magic = re.findall(r'(?<![=\w])\b([2-9]\d{1,})\b', clean_code)
    if len(magic) > 3:
        smells.append(f"Magic numbers found ({len(magic)} occurrences). Use named constants instead.")

    # 4. Functions that are too long (> 40 lines for Python, > 60 for C)
    if lang == 'python':
        fn_starts = [i for i, ln in enumerate(lines) if re.match(r'\s*def\s+', ln)]
        for start in fn_starts:
            base_indent = len(lines[start]) - len(lines[start].lstrip())
            end = start + 1
            while end < len(lines):
                stripped = lines[end].strip()
                if stripped == '':
                    end += 1
                    continue
                cur_indent = len(lines[end]) - len(lines[end].lstrip())
                if cur_indent <= base_indent and stripped:
                    break
                end += 1
            fn_len = end - start
            if fn_len > 40:
                fn_name = re.search(r'def\s+(\w+)', lines[start])
                name = fn_name.group(1) if fn_name else 'unknown'
                smells.append(f"Function '{name}' is too long ({fn_len} lines). Consider breaking it up.")
    else:
        # C: detect large blocks between braces
        depth = 0
        fn_start_line = 0
        fn_name = ''
        for i, ln in enumerate(lines):
            m = re.match(r'^[\w\*\s]+\s+(\w+)\s*\(', ln)
            if m and '{' in ln:
                fn_start_line = i
                fn_name = m.group(1)
                depth = ln.count('{') - ln.count('}')
            elif depth > 0:
                depth += ln.count('{') - ln.count('}')
                if depth == 0:
                    fn_len = i - fn_start_line
                    if fn_len > 60:
                        smells.append(f"Function '{fn_name}' is too long ({fn_len} lines). Consider refactoring.")

    # 5. Duplicate code (repeated adjacent blocks > 5 lines)
    block_size = 5
    line_set = []
    for i in range(len(lines) - block_size):
        block = tuple(ln.strip() for ln in lines[i:i+block_size] if ln.strip())
        if len(block) == block_size:
            if block in line_set:
                smells.append(f"Possible duplicate code block detected around line {i+1}.")
                break
            line_set.append(block)

    # 6. Empty except/catch blocks
    if lang == 'python' and re.search(r'except\s*[^:]*:\s*\n\s*pass', original_code):
        smells.append("Empty except block with 'pass' found. Handle exceptions properly.")
    if lang == 'c' and re.search(r'catch\s*\([^)]*\)\s*\{\s*\}', original_code):
        smells.append("Empty catch block found. Handle exceptions properly.")

    return smells


# ---------------------------------------------------------------------------
# Maintainability Index
# ---------------------------------------------------------------------------

def maintainability_index(loc: int, halstead_volume: float, cyclomatic: int) -> float:
    """Compute the Maintainability Index (MI).

    MI = 171 - 5.2 * ln(V) - 0.23 * CC - 16.2 * ln(LOC)
    Clamped to [0, 100].
    """
    if loc <= 0 or halstead_volume <= 0:
        return 100.0
    mi = 171 - 5.2 * math.log(halstead_volume) - 0.23 * cyclomatic - 16.2 * math.log(loc)
    mi = max(0.0, min(100.0, mi))
    return round(mi, 2)


def mi_grade(mi: float) -> str:
    """Return a letter grade for the Maintainability Index."""
    if mi >= 85:
        return 'A (Highly Maintainable)'
    elif mi >= 65:
        return 'B (Moderately Maintainable)'
    elif mi >= 40:
        return 'C (Hard to Maintain)'
    else:
        return 'D (Very Hard to Maintain)'


# ---------------------------------------------------------------------------
# Energy Estimate
# ---------------------------------------------------------------------------

def energy_estimate(loc: int, loops: int, decisions: int) -> int:
    """Estimate relative energy usage as a proxy metric.

    Higher loops and decision points = more CPU cycles = more energy.
    """
    return int(0.5 * loc + 1.0 * loops + 1.5 * decisions)


def energy_grade(energy: int) -> str:
    """Grade the energy estimate."""
    if energy < 20:
        return '⚡ Very Efficient'
    elif energy < 50:
        return '✅ Efficient'
    elif energy < 100:
        return '⚠️  Moderate'
    else:
        return '🔥 Inefficient'


# ---------------------------------------------------------------------------
# Improvement Suggestions
# ---------------------------------------------------------------------------

def generate_suggestions(metrics: Dict, smells: List[str], language: str) -> List[str]:
    """Generate actionable suggestions based on metrics and smells."""
    lang = language.lower()
    tips = []

    if metrics['Loops'] > 5:
        if lang == 'python':
            tips.append("🔄 Too many loops. Use list comprehensions or built-ins like map/filter to reduce loop count.")
        else:
            tips.append("🔄 Too many loops. Consider using library functions (e.g., memset, memcpy) where possible.")

    if metrics['Cyclomatic Complexity'] > 10:
        tips.append(f"🌀 High cyclomatic complexity ({metrics['Cyclomatic Complexity']}). "
                    "Break large functions into smaller, single-responsibility functions.")

    if metrics['Functions'] == 0 and metrics['Lines of Code'] > 20:
        tips.append("📦 No functions found. Encapsulate logic into named functions for reusability and readability.")

    if metrics['Halstead']['Difficulty'] > 20:
        tips.append(f"🧩 High Halstead difficulty ({metrics['Halstead']['Difficulty']}). "
                    "Simplify expressions and reduce operator variety.")

    if metrics['Energy Estimate'] > 80:
        tips.append("⚡ High energy estimate. Reduce nested loops, simplify conditionals, and cache repeated computations.")

    if metrics['Maintainability Index'] < 65:
        tips.append(f"🛠️  Low maintainability index ({metrics['Maintainability Index']}). "
                    "Refactor complex functions, add comments, and simplify logic.")

    if lang == 'python':
        tips.append("✨ Use Python type hints (e.g., def foo(x: int) -> str) for better readability.")
        if metrics['Lines of Code'] > 50:
            tips.append("📂 Consider splitting code into multiple modules/files for better organisation.")
    else:
        tips.append("📝 Use const and restrict qualifiers in C to help the compiler optimise memory access.")
        tips.append("🔧 Prefer stack allocation over heap (malloc) for small, short-lived data structures.")

    # Add smell-specific tips
    for smell in smells:
        if 'magic number' in smell.lower():
            tips.append("🔢 Replace magic numbers with named #define (C) or constants (Python) for clarity.")
        if 'too long' in smell.lower():
            tips.append("✂️  Split long functions into focused helper functions (Single Responsibility Principle).")
        if 'duplicate' in smell.lower():
            tips.append("♻️  Extract duplicate code into a shared helper function (DRY – Don't Repeat Yourself).")

    return list(dict.fromkeys(tips))  # deduplicate while preserving order


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def analyze_code_quality(code: str, language: str) -> Dict[str, Any]:
    """Full code quality analysis. Returns a rich metrics dictionary."""
    clean = strip_comments(code, language)
    loc = count_loc(clean)
    funcs = count_functions(clean, language)
    loops = count_loops(clean, language)
    decisions = count_decisions(clean, language)
    cc = decisions + 1
    energy = energy_estimate(loc, loops, decisions)
    halstead = halstead_metrics(clean, language)
    mi = maintainability_index(loc, halstead.get('Volume', 1), cc)
    smells = detect_code_smells(code, clean, language)

    metrics = {
        'Lines of Code': loc,
        'Functions': funcs,
        'Loops': loops,
        'Decision Points': decisions,
        'Cyclomatic Complexity': cc,
        'Energy Estimate': energy,
        'Energy Grade': energy_grade(energy),
        'Halstead': halstead,
        'Maintainability Index': mi,
        'Maintainability Grade': mi_grade(mi),
        'Code Smells': smells,
    }

    metrics['Suggestions'] = generate_suggestions(metrics, smells, language)
    return metrics


__all__ = ['analyze_code_quality', 'strip_comments']
