---
description: Run batch-rembg — check setup, test on a small batch, then process all images
---

You help users operate `batch_rembg.py`. Follow these steps in order.

## 1. Check environment

Run these commands and report results:

```
python --version
uv run python -c "import rembg; print('rembg OK')"
ls input/
```

If anything fails, tell the user what to fix and stop.

## 2. Count input images

```
ls input/ | wc -l
```

Report the count. If zero, tell the user to add images to `input/` and stop.

## 3. Test on a small batch

```
uv run python batch_rembg.py --model u2netp --limit 5
```

Report results. Ask the user to check `output/` for quality.

## 4. If quality is poor

Reflective, transparent, or complex objects may need a better model or alpha matting:

```
uv run python batch_rembg.py --model birefnet-general --limit 5
```

If edges are rough or halos appear, add alpha matting:

```
uv run python batch_rembg.py --model birefnet-general --alpha-matting --limit 5
```

Alpha matting can be tuned with `--fg-threshold` (default 240) and `--bg-threshold` (default 10). Lower fg-threshold keeps more foreground detail. Higher bg-threshold removes more background.

`--post-process` cleans up mask edges and can help with jagged outlines.

## 5. Process all images

Only after the user confirms quality is acceptable:

```
uv run python batch_rembg.py
```

Use whatever model and flags worked best in testing. Examples:

- Speed: `--model u2netp`
- Quality: `--model birefnet-general`
- Complex objects: `--model birefnet-general --alpha-matting`
- Resume interrupted run: `--skip-existing`

## Model guide

| Model | Speed | Best for |
|-------|-------|----------|
| `u2netp` | Fast (4-6 img/s) | Simple backgrounds, testing |
| `u2net` | Medium (1.5-2 img/s) | General purpose (default) |
| `birefnet-general` | Slow (0.8-1 img/s) | Reflective/complex objects |

## Notes

- Models download to `~/.u2net/` on first run
- `--dry-run` previews without processing
- `--list-models` shows all 7 available models
- Errors are logged to `error_log.txt`
