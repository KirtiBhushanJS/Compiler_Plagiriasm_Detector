"""main.py
Compiler-Based Structural Plagiarism Detector
==============================================
Cross-Language AST & Subtree Merkle Hashing Engine with:
  - Multiple similarity algorithms (Jaccard, Cosine, LCS)
  - Advanced code quality analysis (Halstead, Cyclomatic Complexity, MI)
  - Code smell detection & improvement suggestions
  - HTML report export
  - Batch folder comparison
  - History logging (JSON)
"""

import os
import json
import glob
from datetime import datetime
from typing import Tuple, Dict, Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.prompt import Prompt, Confirm
from rich.columns import Columns
from rich import box

from c_parser import CToCanonicalParser
from python_parser import PyToCanonicalParser
from similarity import SimilarityEngine
from algorithms import tokenize, combined_score
from code_quality import analyze_code_quality
from report_generator import generate_html_report

# ── Constants ──────────────────────────────────────────────────────────────
HISTORY_FILE = os.path.join(os.path.dirname(__file__), 'history.json')
console = Console()

# ── Helpers ────────────────────────────────────────────────────────────────

def get_parser(filename: str):
    """Detect file extension and return the appropriate parser and language name."""
    ext = os.path.splitext(filename)[1].lower()
    if ext == '.c':
        return CToCanonicalParser(), 'C'
    elif ext in ('.py', '.python'):
        return PyToCanonicalParser(), 'Python'
    else:
        raise ValueError(f"Unsupported file type '{ext}'. Please provide a .c or .py file.")


def load_file(path: str) -> str:
    """Read a source file and return its contents."""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def save_history(entry: Dict[str, Any]):
    """Append a comparison result to history.json."""
    history = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                history = json.load(f)
        except Exception:
            history = []
    history.append(entry)
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)


def load_history() -> list:
    """Load comparison history from history.json."""
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return []


# ── Rich Report Rendering ──────────────────────────────────────────────────

def _score_color(score: float) -> str:
    if score >= 75:
        return 'bold red'
    elif score >= 45:
        return 'bold yellow'
    return 'bold green'


def _score_badge(score: float) -> str:
    if score >= 75:
        return '[bold white on red] 🔴 HIGH RISK OF PLAGIARISM [/bold white on red]'
    elif score >= 45:
        return '[bold black on yellow] 🟡 MODERATE SIMILARITY [/bold black on yellow]'
    return '[bold white on green] 🟢 LOW SIMILARITY / ORIGINAL WORK [/bold white on green]'


def _verdict(score: float) -> str:
    if score >= 75:
        return ('[bold red]Critical Structural Match Found![/bold red]\n'
                'The logic, control flow, and program structure in both files are nearly identical. '
                'It is highly likely that one file was copied from the other or directly translated '
                'across languages.')
    elif score >= 45:
        return ('[bold yellow]Partial Match Detected.[/bold yellow]\n'
                'Both files share significant structural patterns but contain unique sections. '
                'Manual code review is recommended.')
    return ('[bold green]No Significant Copying Found.[/bold green]\n'
            'The internal structure of both code files appears independent and '
            'fundamentally different.')


def render_similarity_panel(file1, lang1, file2, lang2, jaccard, cosine, lcs, combined):
    """Print all similarity metrics in a rich table."""
    color = _score_color(combined)
    border = color.split()[-1]

    # Header
    console.print()
    console.print(Panel.fit(
        '[bold cyan]COMPILER-BASED STRUCTURAL PLAGIARISM DETECTOR[/bold cyan]\n'
        '[italic dim]Cross-Language AST & Multi-Algorithm Similarity Engine[/italic dim]',
        border_style='cyan'
    ))

    # File info
    info = Table(show_header=True, header_style='bold magenta', box=box.SIMPLE)
    info.add_column('Target', style='bold white', width=10)
    info.add_column('File', style='dim white')
    info.add_column('Language', style='bold cyan')
    info.add_row('File 1', file1, lang1)
    info.add_row('File 2', file2, lang2)
    console.print(Panel(info, title='[bold]📁 Input Files[/bold]', border_style='blue'))

    # Algorithm scores table
    algo_table = Table(show_header=True, header_style='bold magenta', box=box.ROUNDED)
    algo_table.add_column('Algorithm', style='white')
    algo_table.add_column('Description', style='dim')
    algo_table.add_column('Score', justify='right', style='bold')
    algo_table.add_row('Jaccard (n-gram)', 'Set overlap of 3-gram token sequences', f'[cyan]{jaccard:.1f}%[/cyan]')
    algo_table.add_row('Cosine Similarity', 'Term-frequency vector angle', f'[cyan]{cosine:.1f}%[/cyan]')
    algo_table.add_row('LCS Ratio', 'Longest Common Subsequence ratio', f'[cyan]{lcs:.1f}%[/cyan]')
    algo_table.add_row('', '', '')
    algo_table.add_row('[bold]Combined Score[/bold]', '[bold]Weighted average (35/30/35)[/bold]', f'[{color}]{combined:.1f}%[/{color}]')

    console.print(Panel(
        f'{_score_badge(combined)}\n\n' + algo_table.__rich_console__.__doc__ if False else '',
        title=f'[{color}]📊 Similarity Analysis[/{color}]',
        border_style=border,
    ))
    # (render table separately for cleaner output)
    console.print(Panel(algo_table, title=f'[{color}]📊 Similarity Scores[/{color}]', border_style=border))
    console.print(Panel(f'{_score_badge(combined)}\n\n{_verdict(combined)}',
                        title='[bold]🏁 Verdict & Findings[/bold]', border_style=border))


def render_quality_panel(filename: str, quality: Dict[str, Any]):
    """Print the code quality analysis for one file."""
    h = quality.get('Halstead', {})
    smells = quality.get('Code Smells', [])
    suggestions = quality.get('Suggestions', [])

    # Metrics table
    mt = Table(show_header=False, box=box.SIMPLE, padding=(0, 1))
    mt.add_column('Metric', style='bold cyan', width=28)
    mt.add_column('Value', style='magenta')
    mt.add_row('Lines of Code', str(quality['Lines of Code']))
    mt.add_row('Functions / Methods', str(quality['Functions']))
    mt.add_row('Loop Constructs', str(quality['Loops']))
    mt.add_row('Decision Points', str(quality['Decision Points']))
    mt.add_row('Cyclomatic Complexity', str(quality['Cyclomatic Complexity']))
    mt.add_row('─' * 25, '─' * 12)
    mt.add_row('Halstead Volume', str(h.get('Volume', 0)))
    mt.add_row('Halstead Difficulty', str(h.get('Difficulty', 0)))
    mt.add_row('Halstead Bug Estimate', str(h.get('Bugs Estimate', 0)))
    mt.add_row('─' * 25, '─' * 12)
    mt.add_row('Energy Estimate', f"{quality['Energy Estimate']} — {quality['Energy Grade']}")
    mt.add_row('Maintainability Index', f"{quality['Maintainability Index']} / 100")
    mt.add_row('Maintainability Grade', quality['Maintainability Grade'])

    console.print(Panel(mt, title=f'[bold]📋 Code Quality — {os.path.basename(filename)}[/bold]',
                        border_style='bright_blue'))

    # Code smells
    if smells:
        smell_text = '\n'.join(f'  [bold yellow]⚠[/bold yellow]  {s}' for s in smells)
        console.print(Panel(smell_text, title='[bold yellow]⚠️  Code Smells Detected[/bold yellow]',
                            border_style='yellow'))

    # Suggestions
    if suggestions:
        tip_text = '\n'.join(f'  {t}' for t in suggestions)
        console.print(Panel(tip_text, title='[bold green]💡 Improvement Suggestions[/bold green]',
                            border_style='green'))


def render_efficiency_verdict(file1_path: str, lang1: str, q1: Dict[str, Any], file2_path: str, lang2: str, q2: Dict[str, Any]):
    """Renders a comparative efficiency verdict explaining which code is more efficient and why."""
    name1 = os.path.basename(file1_path)
    name2 = os.path.basename(file2_path)

    e1 = q1.get('Energy Estimate', 0)
    e2 = q2.get('Energy Estimate', 0)
    cc1 = q1.get('Cyclomatic Complexity', 1)
    cc2 = q2.get('Cyclomatic Complexity', 1)
    mi1 = q1.get('Maintainability Index', 0)
    mi2 = q2.get('Maintainability Index', 0)
    loc1 = q1.get('Lines of Code', 0)
    loc2 = q2.get('Lines of Code', 0)
    loops1 = q1.get('Loops', 0)
    loops2 = q2.get('Loops', 0)
    vol1 = q1.get('Halstead', {}).get('Volume', 0)
    vol2 = q2.get('Halstead', {}).get('Volume', 0)

    # Compute a composite efficiency score (lower is better for energy/complexity/volume, higher better for MI)
    score1 = 0
    score2 = 0
    reasons = []

    # 1. Energy
    if e1 < e2:
        score1 += 2
        reasons.append(f"• [bold green]{name1}[/bold green] consumes less estimated energy ({e1} vs {e2}).")
    elif e2 < e1:
        score2 += 2
        reasons.append(f"• [bold green]{name2}[/bold green] consumes less estimated energy ({e2} vs {e1}).")

    # 2. Loops & Control flow
    if loops1 < loops2:
        score1 += 1
        reasons.append(f"• [bold green]{name1}[/bold green] has fewer looping structures ({loops1} vs {loops2}), reducing CPU branch cycles.")
    elif loops2 < loops1:
        score2 += 1
        reasons.append(f"• [bold green]{name2}[/bold green] has fewer looping structures ({loops2} vs {loops1}), reducing CPU branch cycles.")

    # 3. Cyclomatic complexity
    if cc1 < cc2:
        score1 += 1
        reasons.append(f"• [bold green]{name1}[/bold green] has lower cyclomatic complexity ({cc1} vs {cc2}), leading to cleaner execution branches.")
    elif cc2 < cc1:
        score2 += 1
        reasons.append(f"• [bold green]{name2}[/bold green] has lower cyclomatic complexity ({cc2} vs {cc1}), leading to cleaner execution branches.")

    # 4. Maintainability Index
    if mi1 > mi2:
        score1 += 1
        reasons.append(f"• [bold green]{name1}[/bold green] has higher maintainability index ({mi1:.1f} vs {mi2:.1f}).")
    elif mi2 > mi1:
        score2 += 1
        reasons.append(f"• [bold green]{name2}[/bold green] has higher maintainability index ({mi2:.1f} vs {mi1:.1f}).")

    # 5. Information volume
    if vol1 < vol2 and vol1 > 0:
        reasons.append(f"• [bold green]{name1}[/bold green] requires lower computational volume ({vol1:.1f} vs {vol2:.1f} Halstead volume).")
    elif vol2 < vol1 and vol2 > 0:
        reasons.append(f"• [bold green]{name2}[/bold green] requires lower computational volume ({vol2:.1f} vs {vol1:.1f} Halstead volume).")

    # Final verdict
    if score1 > score2:
        winner = name1
        winner_color = "bold green"
        summary_line = f"[{winner_color}]🏆 Winner: {name1}[/{winner_color}] is demonstrably more efficient."
    elif score2 > score1:
        winner = name2
        winner_color = "bold green"
        summary_line = f"[{winner_color}]🏆 Winner: {name2}[/{winner_color}] is demonstrably more efficient."
    else:
        winner_color = "bold yellow"
        summary_line = f"[{winner_color}]⚖️ Both implementations display comparable computational efficiency.[/{winner_color}]"

    # Comparison summary table
    cmp_table = Table(show_header=True, header_style="bold magenta", box=box.ROUNDED)
    cmp_table.add_column("Efficiency Metric", style="white")
    cmp_table.add_column(f"{name1} ({lang1})", justify="center", style="cyan")
    cmp_table.add_column(f"{name2} ({lang2})", justify="center", style="magenta")
    cmp_table.add_column("Advantage", justify="center", style="bold")

    def adv(val1, val2, lower_is_better=True):
        if val1 == val2:
            return "[dim]Tie[/dim]"
        if lower_is_better:
            return f"[green]{name1}[/green]" if val1 < val2 else f"[green]{name2}[/green]"
        else:
            return f"[green]{name1}[/green]" if val1 > val2 else f"[green]{name2}[/green]"

    cmp_table.add_row("Lines of Code (LOC)", str(loc1), str(loc2), adv(loc1, loc2, True))
    cmp_table.add_row("Loop Constructs", str(loops1), str(loops2), adv(loops1, loops2, True))
    cmp_table.add_row("Decision Points", str(q1.get('Decision Points', 0)), str(q2.get('Decision Points', 0)), adv(q1.get('Decision Points', 0), q2.get('Decision Points', 0), True))
    cmp_table.add_row("Cyclomatic Complexity", str(cc1), str(cc2), adv(cc1, cc2, True))
    cmp_table.add_row("Halstead Volume", f"{vol1:.1f}", f"{vol2:.1f}", adv(vol1, vol2, True))
    cmp_table.add_row("Energy Proxy", f"{e1} ({q1.get('Energy Grade', '')})", f"{e2} ({q2.get('Energy Grade', '')})", adv(e1, e2, True))
    cmp_table.add_row("Maintainability Index", f"{mi1:.1f}", f"{mi2:.1f}", adv(mi1, mi2, False))

    brief_text = "\n".join(reasons) if reasons else "Both files have virtually identical complexity profiles."
    full_content = f"{summary_line}\n\n[bold underline]Key Efficiency Drivers:[/bold underline]\n{brief_text}\n"

    console.print()
    console.print(Panel(cmp_table, title="[bold cyan]⚡ Comparative Efficiency Breakdown[/bold cyan]", border_style="cyan"))
    console.print(Panel(full_content, title="[bold green]🏆 Efficiency Verdict & Brief[/bold green]", border_style="green"))


# ── Core Analysis ──────────────────────────────────────────────────────────

def run_analysis(file1_path: str, file2_path: str, export_html: bool = False):
    """Perform full analysis on two files and display results."""
    with Progress(
        SpinnerColumn(),
        TextColumn('[progress.description]{task.description}'),
        BarColumn(),
        transient=True,
        console=console,
    ) as progress:
        t = progress.add_task('[cyan]Loading files...', total=5)

        code1 = load_file(file1_path)
        parser1, lang1 = get_parser(file1_path)
        progress.advance(t)

        code2 = load_file(file2_path)
        parser2, lang2 = get_parser(file2_path)
        progress.advance(t)

        progress.update(t, description='[cyan]Parsing ASTs...')
        ast1 = parser1.parse(code1)
        ast2 = parser2.parse(code2)
        progress.advance(t)

        progress.update(t, description='[cyan]Computing similarity scores...')
        tokens1 = tokenize(code1)
        tokens2 = tokenize(code2)
        jaccard, cosine, lcs, combined = combined_score(tokens1, tokens2)
        progress.advance(t)

        progress.update(t, description='[cyan]Analysing code quality & efficiency...')
        quality1 = analyze_code_quality(code1, lang1)
        quality2 = analyze_code_quality(code2, lang2)
        progress.advance(t)

    # Render terminal output
    render_similarity_panel(file1_path, lang1, file2_path, lang2, jaccard, cosine, lcs, combined)
    render_quality_panel(file1_path, quality1)
    render_quality_panel(file2_path, quality2)

    # Comparative Efficiency Analysis
    render_efficiency_verdict(file1_path, lang1, quality1, file2_path, lang2, quality2)

    # Save history
    save_history({
        'timestamp': datetime.now().isoformat(),
        'file1': file1_path, 'lang1': lang1,
        'file2': file2_path, 'lang2': lang2,
        'jaccard': jaccard, 'cosine': cosine,
        'lcs': lcs, 'combined': combined,
        'mi1': quality1['Maintainability Index'],
        'mi2': quality2['Maintainability Index'],
    })
    console.print('[dim]✔ Result saved to history.[/dim]')

    # HTML export
    if export_html:
        out = generate_html_report(
            file1_path, lang1, file2_path, lang2,
            jaccard, cosine, lcs, combined,
            quality1, quality2,
            output_dir=os.path.dirname(file1_path) or '.'
        )
        console.print(f'[bold green]✔ HTML report saved:[/bold green] {out}')


# ── Batch Mode ─────────────────────────────────────────────────────────────

def run_batch(folder: str, export_html: bool = False):
    """Compare all .c and .py files in a folder pairwise."""
    files = glob.glob(os.path.join(folder, '*.c')) + glob.glob(os.path.join(folder, '*.py'))
    if len(files) < 2:
        console.print('[bold red]Error:[/bold red] Need at least 2 .c or .py files in the folder.')
        return

    console.print(f'\n[bold cyan]Batch Mode:[/bold cyan] Found {len(files)} files — running pairwise comparison.\n')

    results = []
    for i in range(len(files)):
        for j in range(i + 1, len(files)):
            f1, f2 = files[i], files[j]
            try:
                code1 = load_file(f1)
                code2 = load_file(f2)
                _, lang1 = get_parser(f1)
                _, lang2 = get_parser(f2)
                tokens1 = tokenize(code1)
                tokens2 = tokenize(code2)
                jac, cos, lcs, comb = combined_score(tokens1, tokens2)
                results.append((f1, lang1, f2, lang2, jac, cos, lcs, comb))
            except Exception as e:
                console.print(f'[yellow]Skipped {os.path.basename(f1)} vs {os.path.basename(f2)}: {e}[/yellow]')

    # Summary table
    tbl = Table(title='Batch Comparison Results', box=box.ROUNDED, header_style='bold magenta')
    tbl.add_column('File 1', style='dim')
    tbl.add_column('File 2', style='dim')
    tbl.add_column('Jaccard', justify='right')
    tbl.add_column('Cosine', justify='right')
    tbl.add_column('LCS', justify='right')
    tbl.add_column('Combined', justify='right', style='bold')
    tbl.add_column('Risk', justify='center')

    results.sort(key=lambda r: r[7], reverse=True)
    for f1, l1, f2, l2, j, c, l, comb in results:
        risk = '[red]HIGH[/red]' if comb >= 75 else ('[yellow]MED[/yellow]' if comb >= 45 else '[green]LOW[/green]')
        tbl.add_row(
            os.path.basename(f1), os.path.basename(f2),
            f'{j:.1f}%', f'{c:.1f}%', f'{l:.1f}%',
            f'{comb:.1f}%', risk
        )
    console.print(tbl)

    if export_html and results:
        # Export the highest-risk pair
        f1, l1, f2, l2, j, c, l, comb = results[0]
        q1 = analyze_code_quality(load_file(f1), l1)
        q2 = analyze_code_quality(load_file(f2), l2)
        out = generate_html_report(f1, l1, f2, l2, j, c, l, comb, q1, q2, output_dir=folder)
        console.print(f'[bold green]✔ HTML report for highest-risk pair:[/bold green] {out}')


# ── History Viewer ─────────────────────────────────────────────────────────

def show_history():
    """Display the last 10 comparison results from history.json."""
    history = load_history()
    if not history:
        console.print('[yellow]No history found. Run a comparison first.[/yellow]')
        return

    tbl = Table(title='Comparison History (last 10)', box=box.ROUNDED, header_style='bold magenta')
    tbl.add_column('Date/Time', style='dim')
    tbl.add_column('File 1')
    tbl.add_column('File 2')
    tbl.add_column('Combined %', justify='right', style='bold')
    tbl.add_column('Risk', justify='center')

    for entry in reversed(history[-10:]):
        comb = entry.get('combined', 0)
        risk = '[red]HIGH[/red]' if comb >= 75 else ('[yellow]MED[/yellow]' if comb >= 45 else '[green]LOW[/green]')
        tbl.add_row(
            entry.get('timestamp', '')[:19],
            os.path.basename(entry.get('file1', '')),
            os.path.basename(entry.get('file2', '')),
            f"{comb:.1f}%", risk
        )
    console.print(tbl)


# ── Main Menu ──────────────────────────────────────────────────────────────

BANNER = """[bold cyan]
 ██████╗ ██╗      █████╗  ██████╗ ██╗ █████╗ ██████╗ ██╗███████╗███╗   ███╗
 ██╔══██╗██║     ██╔══██╗██╔════╝ ██║██╔══██╗██╔══██╗██║██╔════╝████╗ ████║
 ██████╔╝██║     ███████║██║  ███╗██║███████║██████╔╝██║███████╗██╔████╔██║
 ██╔═══╝ ██║     ██╔══██║██║   ██║██║██╔══██║██╔══██╗██║╚════██║██║╚██╔╝██║
 ██║     ███████╗██║  ██║╚██████╔╝██║██║  ██║██║  ██║██║███████║██║ ╚═╝ ██║
 ╚═╝     ╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚══════╝╚═╝     ╚═╝
[/bold cyan]
[bold white]         COMPILER-BASED STRUCTURAL PLAGIARISM DETECTOR[/bold white]
[dim]   Cross-Language AST · Multi-Algorithm · Code Quality Analysis · HTML Report[/dim]"""


def main():
    console.clear()
    console.print(Panel.fit(BANNER, border_style='cyan'))

    while True:
        console.print()
        console.rule('[bold cyan]Main Menu[/bold cyan]')
        console.print('[bold white] 1.[/bold white] Compare two files')
        console.print('[bold white] 2.[/bold white] Batch compare a folder')
        console.print('[bold white] 3.[/bold white] View comparison history')
        console.print('[bold white] 4.[/bold white] Exit')
        console.print()

        choice = Prompt.ask('[bold yellow]Select an option[/bold yellow]', choices=['1', '2', '3', '4'])

        if choice == '1':
            console.print()
            file1 = Prompt.ask('[bold yellow]► File 1 path[/bold yellow]').strip()
            file2 = Prompt.ask('[bold yellow]► File 2 path[/bold yellow]').strip()
            html = Confirm.ask('[bold yellow]Export HTML report?[/bold yellow]', default=False)
            try:
                run_analysis(file1, file2, export_html=html)
            except FileNotFoundError as e:
                console.print(f'\n[bold red]Error:[/bold red] File not found — {e.filename}')
            except Exception as e:
                console.print(f'\n[bold red]Error:[/bold red] {e}')

        elif choice == '2':
            folder = Prompt.ask('[bold yellow]► Folder path[/bold yellow]').strip()
            html = Confirm.ask('[bold yellow]Export HTML report for top pair?[/bold yellow]', default=False)
            try:
                run_batch(folder, export_html=html)
            except Exception as e:
                console.print(f'\n[bold red]Error:[/bold red] {e}')

        elif choice == '3':
            show_history()

        elif choice == '4':
            console.print('\n[bold cyan]Goodbye! 👋[/bold cyan]\n')
            break


if __name__ == '__main__':
    main()