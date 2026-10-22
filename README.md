# Compiler-Based Cross-Language Structural Plagiarism Detector & Code Efficiency Evaluator

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Course: BCSE307P](https://img.shields.io/badge/Course-BCSE307P%20Compiler%20Design-green.svg)](#)

An industrial-grade, cross-language source code structural plagiarism detection and static code quality evaluation system developed for the **BCSE307P Compiler Design Lab** at **Vellore Institute of Technology (VIT)**.

---

## 📌 Problem & Overview

Traditional plagiarism tools (such as MOSS, JPlag, and Diff) operate at the character or lexical token level and are fundamentally restricted to single-language evaluations. When students transliterate algorithms across programming languages (e.g., converting an imperative C assignment into Python), conventional tools fail due to diverging keyword sets, disparate syntax specifications, and distinct runtime environments.

This framework applies **Compiler Front-End Intermediate Representation (IR)** techniques to resolve this dilemma:
1. Heterogeneous source files (C and Python) are parsed into unified, language-agnostic **Canonical Abstract Syntax Trees (AST)**.
2. Surface modifications (variable renaming, whitespace perturbation, comment injection, and loop rewriting) are systematically normalized.
3. A **Tri-Algorithm Similarity Engine** (Jaccard N-Grams, Cosine TF-IDF, and Space-Optimized Dynamic Programming LCS) computes an objective structural similarity score.
4. An integrated **Software Quality & Green Computing Suite** evaluates Halstead Software Science, McCabe Cyclomatic Complexity, Maintainability Index ($MI$), and a microarchitectural Static Energy Consumption Proxy.
5. An **Automated Comparative Efficiency Evaluator** compares both submissions side-by-side, determines the more efficient implementation, and generates a causal technical brief.

---

## 🚀 Key Features

* **Cross-Language Canonical AST IR:** Dual compiler front-ends (`c_parser.py` and `python_parser.py`) map C syntax and Python ASTs into isomorphic semantic node hierarchies (`BLOCK`, `LOOP`, `BRANCH`, `ASSIGN`, `BIN_OP`, `RETURN`).
* **Tri-Metric Multi-Algorithm Similarity:**
  * **Jaccard 3-Gram Overlap (35%):** Captures localized sub-block statement preservation.
  * **Term-Frequency Cosine Alignment (30%):** Measures vocabulary distribution independent of file length.
  * **Space-Optimized LCS Ratio (35%):** Alternating two-row DP ($O(\min(N, M))$ memory) tracking global chronological execution order.
* **Green Computing Static Energy Proxy:** Microarchitecturally justified static model quantifying ALU cycles, loop execution, and branch misprediction penalties:
  $$\text{Energy Proxy} = \lfloor 0.5 \cdot LOC + 1.0 \cdot \text{Loops} + 1.5 \cdot \text{Decisions} \rfloor$$
* **Halstead Software Science Suite:** Measures program vocabulary ($\eta$), length ($N$), volume ($V$), difficulty ($D$), effort ($E$), and estimated remaining defects ($B = V / 3000$).
* **McCabe Cyclomatic Complexity & Maintainability Index (MI):** Evaluates independent execution paths and overall code health on a standard 0–100 scale.
* **Code Smell & Antipattern Detection:** Identifies deep nesting ($>3$ levels), long functions ($>40$ lines), magic numbers, duplicate blocks, and empty exception handlers.
* **Comparative Efficiency Verdict Engine:** Automatically synthesizes a comparative metric breakdown and crowns an objective winner with explanatory rationale.
* **Interactive Terminal CLI & HTML Reporting:** Built using the `rich` library with ASCII banners, animated progress spinners, and exportable dark-themed HTML reports.

---

## 🏗️ System Architecture

```
[Source Code 1: C]      --> [C Lexer / Canonical Parser]  --> [Canonical AST] \
                                                                               --> [Multi-Algorithm Similarity Engine] --> Report & Verdict
[Source Code 2: Python] --> [Python AST Visitor Linearizer]--> [Canonical AST] /
                                                                       │
                                                       [Static Quality & Green Energy]
                                                       (Halstead, Cyclomatic, MI, Smells)
```

---

## 📂 Repository Structure

```
compiler_plagiarism_detector/
├── main.py              # CLI entry point, interactive menu & comparative evaluator
├── c_parser.py          # C lexical stripper and canonical AST node generator
├── python_parser.py     # Python order-preserving AST Visitor linearizer
├── algorithms.py        # Jaccard, Cosine, and space-optimized 2-row LCS similarity engine
├── code_quality.py      # Halstead metrics, McCabe Cyclomatic Complexity, MI & Code Smells
├── efficiency.py        # Standalone static efficiency & green energy proxy analyzer
├── report_generator.py  # Standalone responsive HTML report synthesizer
├── diff_viewer.py       # Token-level diff viewer utility
├── test_large_c.c       # Industrial matrix transformation benchmark (C)
├── test_large_py.py     # Industrial matrix transformation benchmark (Python)
├── test1.c              # Elementary control-flow loop benchmark (C)
├── test2.py             # Elementary control-flow loop benchmark (Python)
├── test3.c              # Negative control independent benchmark (C)
├── test4.py             # Negative control independent benchmark (Python)
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation
```

---

## ⚙️ Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/jskirtibhushan/compiler_plagiarism_detector.git
   cd compiler_plagiarism_detector
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

---

## 💻 Usage

Launch the interactive CLI dashboard:
```bash
python3 main.py
```

### Main Menu Options:
1. **Compare two files:** Enter the relative or absolute paths for File 1 (C/Python) and File 2 (C/Python). Optionally export a standalone HTML report.
2. **Batch compare a folder:** Analyzes all `.c` and `.py` files in a designated folder pairwise, generating a risk matrix table.
3. **View comparison history:** Displays longitudinal analysis logs stored in `history.json`.
4. **Exit.**

---

## 🧪 Benchmark Results

Tested on an industrial multi-stage matrix transformation and convergence pipeline (`test_large_c.c` vs `test_large_py.py`):

| Metric | test_large_c.c (C) | test_large_py.py (Python) | Winner / Advantage |
| :--- | :---: | :---: | :---: |
| **Lines of Code (LOC)** | 65 | 49 | `test_large_py.py` (More concise) |
| **Loop Constructs** | 10 | 18 | `test_large_c.c` (Fewer loop branches) |
| **Decision Points** | 2 | 3 | `test_large_c.c` (Cleaner branch flow) |
| **Cyclomatic Complexity** | 3 | 4 | `test_large_c.c` (Lower path complexity) |
| **Halstead Volume** | 2518.9 | 1886.8 | `test_large_py.py` (Lower volume entropy) |
| **Energy Proxy** | **45 (✅ Efficient)** | **47 (✅ Efficient)** | `test_large_c.c` (Lower execution cost) |
| **Maintainability Index** | 61.96 (Grade C) | 67.81 (Grade B) | `test_large_py.py` (Higher maintainability) |
| **Cosine Similarity** | \multicolumn{2}{c|}{**70.51%**} | Structural similarity detected |
| **LCS Sequence Ratio**| \multicolumn{2}{c|}{**53.67%**} | Sequential logic alignment |
| **Combined Score** | \multicolumn{2}{c|}{**48.63% (MODERATE MATCH)**} | Cross-language port flagged |

**Efficiency Verdict:** `🏆 Winner: test_large_c.c is demonstrably more efficient` (lower estimated energy consumption, fewer loop branch penalties, and reduced cyclomatic complexity).

---

## 👥 Contributors (Team Members)

* **Sarveshwar N S** (Reg No: `24BCE0018`) - Compiler Front-End, AST Canonicalization & Parser Architecture
* **J S Kirti Bhushan** (Reg No: `24BCE0320`) - Multi-Algorithm Similarity Engine, Dynamic Fusion & CLI Orchestration
* **Austin Venansius S** (Reg No: `24BCE0672`) - Halstead Complexity Science, Green Computing & Comparative Verdict Engine

**Under the Supervision of:**
* **Prof. MUTHUNAGAI S U**, Assistant Professor Sr. Grade-2, School of Computer Science Engineering and Information Systems, **Vellore Institute of Technology (VIT)**.

---

## 📄 License
This project is open-source and available under the [MIT License](LICENSE).
