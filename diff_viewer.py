"""diff_viewer.py
Token-level diff viewer for the Plagiarism Detector.

Highlights which regions of two source files share similar token sequences
using the Longest Common Subsequence (LCS) algorithm.

Output:
  - Rich terminal side-by-side diff with matched regions highlighted
  - Each matching block labelled with its similarity contribution
"""
import os
import re
from typing import List, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

console = Console()


# ── Tokenisation ─────────────────────────────────────────────────────────────

def tokenize_with_positions(code: str) -> List[Tuple[str, int]]:
    """Return list of (token, line_number) pairs from source code."""
    tokens = []
    for i, line in enumerate(code.splitlines(), start=1):
        # Remove string literals and normalise numbers
        line_clean = re.sub(r'".*?"|\'.*?\'', '"STR"', line)
        line_clean = re.sub(r'\b\d+(\.\d+)?\b', 'NUM', line_clean)
        for tok in re.findall(r'[a-zA-Z_]\w*|[+\-*/=<>!&|^~%]+|[(){}\[\];,.]', line_clean):
            tokens.append((tok, i))
    return tokens


# ── LCS-based matching ────────────────────────────────────────────────────────

def find_matching_blocks(
    tokens1: List[Tuple[str, int]],
    tokens2: List[Tuple[str, int]],
    min_block: int = 4
) -> List[Tuple[int, int, int]]:
    """
    Find matching token blocks using a sliding window LCS approach.

    Returns list of (start_line_in_file1, start_line_in_file2, block_length_in_tokens)
    for each matched block of at least `min_block` tokens.
    """
    seq1 = [t for t, _ in tokens1]
    seq2 = [t for t, _ in tokens2]
    n, m = len(seq1), len(seq2)

    # Build LCS table (capped for performance)
    cap = 400
    s1 = seq1[:cap]
    s2 = seq2[:cap]
    n, m = len(s1), len(s2)

    # DP table
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

    # Traceback to find matching blocks
    blocks = []
    i, j = n, m
    current_block = []

    while i > 0 and j > 0:
        if s1[i - 1] == s2[j - 1]:
            current_block.append((i - 1, j - 1))
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            if len(current_block) >= min_block:
                blocks.append(current_block[:])
            current_block = []
            i -= 1
        else:
            if len(current_block) >= min_block:
                blocks.append(current_block[:])
            current_block = []
            j -= 1

    if len(current_block) >= min_block:
        blocks.append(current_block)

    # Convert token indices to line numbers
    result = []
    for block in blocks:
        block_sorted = sorted(block, key=lambda x: x[0])
        idx1_start = block_sorted[0][0]
        idx2_start = block_sorted[0][1]
        line1 = tokens1[idx1_start][1] if idx1_start < len(tokens1) else 0
        line2 = tokens2[idx2_start][1] if idx2_start < len(tokens2) else 0
        result.append((line1, line2, len(block)))

    # Sort by file1 line number
    result.sort(key=lambda x: x[0])
    return result


# ── Line extraction ───────────────────────────────────────────────────────────

def get_lines(code: str) -> List[str]:
    return code.splitlines()


# ── Rich Diff Rendering ───────────────────────────────────────────────────────

def render_diff(
    file1: str, code1: str,
    file2: str, code2: str,
    min_block: int = 4,
    context_lines: int = 2
):
    """
    Print a rich terminal side-by-side diff showing matching code regions.

    Args:
        file1, code1: Path and content of the first file.
        file2, code2: Path and content of the second file.
        min_block: Minimum number of matching tokens to show a block.
        context_lines: Number of surrounding lines to show around each match.
    """
    tokens1 = tokenize_with_positions(code1)
    tokens2 = tokenize_with_positions(code2)
    blocks = find_matching_blocks(tokens1, tokens2, min_block=min_block)

    lines1 = get_lines(code1)
    lines2 = get_lines(code2)

    if not blocks:
        console.print(Panel(
            '[bold green]No significant matching code regions found.[/bold green]\n'
            'The two files appear structurally independent.',
            title='🔍 Token-Level Diff',
            border_style='green'
        ))
        return


    console.print()
    console.print(Panel.fit(
        f'[bold cyan]🔍 Token-Level Diff Viewer[/bold cyan]\n'
        f'[dim]{os.path.basename(file1)}  ↔  {os.path.basename(file2)}[/dim]\n'
        f'[yellow]{len(blocks)} matching region(s) found[/yellow]',
        border_style='cyan'
    ))

    for idx, (line1, line2, tok_count) in enumerate(blocks, 1):
        # Gather context lines for each file
        def extract(lines, center, ctx):
            start = max(0, center - ctx - 1)
            end = min(len(lines), center + ctx)
            return start, end, lines[start:end]

        s1, e1, chunk1 = extract(lines1, line1, context_lines)
        s2, e2, chunk2 = extract(lines2, line2, context_lines)

        # Build a two-column table
        tbl = Table(
            title=f'[yellow]Match #{idx}[/yellow]  [dim]~{tok_count} matching tokens[/dim]',
            box=box.ROUNDED,
            show_lines=True,
            header_style='bold magenta',
            expand=True,
        )
        tbl.add_column(
            f'[cyan]{os.path.basename(file1)}[/cyan]  [dim](lines {s1+1}–{e1})[/dim]',
            style='white', ratio=1
        )
        tbl.add_column(
            f'[cyan]{os.path.basename(file2)}[/cyan]  [dim](lines {s2+1}–{e2})[/dim]',
            style='white', ratio=1
        )

        max_rows = max(len(chunk1), len(chunk2))
        for r in range(max_rows):
            ln1_no = s1 + r + 1
            ln2_no = s2 + r + 1

            cell1 = Text()
            cell2 = Text()

            if r < len(chunk1):
                is_match_line1 = (ln1_no == line1)
                style1 = 'bold on dark_green' if is_match_line1 else ''
                cell1.append(f'{ln1_no:>4}  ', style='dim')
                cell1.append(chunk1[r], style=style1)
            
            if r < len(chunk2):
                is_match_line2 = (ln2_no == line2)
                style2 = 'bold on dark_green' if is_match_line2 else ''
                cell2.append(f'{ln2_no:>4}  ', style='dim')
                cell2.append(chunk2[r], style=style2)

            tbl.add_row(cell1, cell2)

        console.print(tbl)

    # Summary panel
    total_matched_tokens = sum(b[2] for b in blocks)
    console.print(Panel(
        f'[bold]Total matching blocks:[/bold] {len(blocks)}\n'
        f'[bold]Total matching tokens:[/bold] {total_matched_tokens}\n\n'
        f'[dim]Highlighted lines (dark green) are the start of each matching region.[/dim]\n'
        f'[dim]Expand context_lines parameter to see more surrounding code.[/dim]',
        title='[bold cyan]📊 Diff Summary[/bold cyan]',
        border_style='cyan'
    ))


__all__ = ['render_diff', 'find_matching_blocks', 'tokenize_with_positions']
