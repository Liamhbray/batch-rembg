# Contributing to batch-rembg

## Getting Started

```bash
gh repo clone Liamhbray/batch-rembg
cd batch-rembg
uv sync
```

## Development

```bash
uv run python batch_rembg.py --dry-run        # Verify setup
uv run python batch_rembg.py --limit 5         # Test on a few images
uv run ruff check .                            # Lint
uv run ruff format .                           # Format
```

## Making Changes

1. Fork the repo and create a branch from `main`
2. Make your changes
3. Ensure `ruff check .` and `ruff format --check .` pass
4. Test with real images (add test images to `input/`, they're gitignored)
5. Open a pull request

## Guidelines

- This is a thin wrapper around [rembg](https://github.com/danielgatis/rembg) — keep it simple
- All image processing goes through rembg's `remove()` function
- CLI arguments should follow existing patterns (`-short`, `--long`)
- Keep `batch_rembg.py` as a single self-contained script

## Reporting Bugs

Use the [bug report template](https://github.com/Liamhbray/batch-rembg/issues/new?template=bug_report.md). Include:

- Python version (`python --version`)
- OS and architecture
- The command you ran
- Full error output
