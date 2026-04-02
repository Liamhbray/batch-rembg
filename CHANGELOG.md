# Changelog

## 0.1.0

### Features

- Batch background removal using [rembg](https://github.com/danielgatis/rembg) with ONNX Runtime (CPU)
- 7 model options: `u2net`, `u2netp`, `birefnet-general`, `u2net_human_seg`, `u2net_cloth_seg`, `silueta`, `isnet-general-use`
- Resume capability with `--skip-existing`
- Dry-run mode for previewing work
- Filename pattern filtering
- Alpha matting support for complex edges
- Real-time progress tracking with ETA
- Error logging to file
