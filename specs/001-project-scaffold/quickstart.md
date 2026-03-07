# Quickstart: bookmarkcli Development Setup

**Feature**: 001-project-scaffold  
**Last updated**: 2026-03-07

---

## Prerequisites

- Python ≥ 3.11 installed and available on `PATH`
- [`uv`](https://docs.astral.sh/uv/) installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Git

---

## 1. Clone and Install

```bash
git clone <repository-url>
cd bookmark-mgr

# Install all dependencies (runtime + dev) and the package in editable mode
uv sync
```

This command:
- Creates a `.venv/` virtual environment if it does not exist
- Installs runtime dependencies (`click`) and dev dependencies (`pytest`, `aiosqlite`)
- Installs `bookmarkcli` as an editable package so `src/bookmarkcli/` changes are immediately reflected

---

## 2. Verify the CLI Entry Point

```bash
uv run bookmarkcli --help
```

Expected output:

```
Usage: bookmarkcli [OPTIONS] COMMAND [ARGS]...

  Bookmark manager CLI.

Options:
  --help  Show this message and exit.
```

---

## 3. Run the Test Suite

```bash
uv run pytest -q
```

Expected output (zero tests collected):

```
no tests ran in 0.00s
```

Exit code is `0` — the `conftest.py` at the repository root normalizes pytest's exit code 5 ("no tests collected") to 0.

---

## 4. Project Layout

```text
bookmark-mgr/
├── pyproject.toml          # Build config, deps, entry points, pytest config
├── uv.lock                 # Locked dependency graph (commit this file)
├── conftest.py             # Root-level pytest plugin (exit-code normalization)
├── src/
│   └── bookmarkcli/
│       ├── __init__.py     # Package namespace
│       └── cli.py          # Click entry point
└── tests/
    └── __init__.py         # Test package marker
```

---

## 5. Common Commands

| Task | Command |
|------|---------|
| Install / sync deps | `uv sync` |
| Run CLI | `uv run bookmarkcli [ARGS]` |
| Run tests | `uv run pytest -q` |
| Run tests verbosely | `uv run pytest -v` |
| Add a runtime dependency | `uv add <package>` |
| Add a dev-only dependency | `uv add --dev <package>` |
| Lock dependencies | `uv lock` |

---

## 6. Troubleshooting

**`bookmarkcli: command not found`**  
Run `uv sync` to install the package and its entry point script. Then use `uv run bookmarkcli` or activate the venv: `source .venv/bin/activate`.

**`ModuleNotFoundError: No module named 'bookmarkcli'`**  
The package must be installed before importing. Run `uv sync`.

**pytest exits with code 5**  
This should not happen because `conftest.py` normalizes it to 0. If you see code 5, verify `conftest.py` is present at the repository root (not only inside `tests/`).
