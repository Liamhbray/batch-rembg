#!/usr/bin/env python3
"""
batch-rembg

Processes images and removes backgrounds with transparent PNG output.

Features:
- Session reuse for efficient processing
- Real-time progress tracking with ETA
- Error handling and logging
- Memory-efficient processing
- CLI arguments for flexibility
- Resume capability (skip existing)
- Dry-run mode for validation
"""

import argparse
import sys
import time
from datetime import timedelta
from pathlib import Path

from rembg import new_session, remove

# Default configuration
DEFAULT_INPUT_DIR = "input"
DEFAULT_OUTPUT_DIR = "output"
DEFAULT_ERROR_LOG = "error_log.txt"
DEFAULT_MODEL = "u2net"

# Supported image extensions (lowercase, matched case-insensitively)
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

# Available models with descriptions
MODELS = {
    "u2net": "Balanced speed/quality (default, ~176MB)",
    "u2netp": "Faster, lighter weight (~4.7MB)",
    "u2net_human_seg": "Optimized for human subjects",
    "u2net_cloth_seg": "Optimized for clothing",
    "silueta": "Good general purpose alternative",
    "isnet-general-use": "IS-Net model for general use",
    "birefnet-general": "Highest quality, slower (~973MB)",
}


def format_time(seconds):
    """Format seconds into human-readable time string."""
    return str(timedelta(seconds=int(seconds)))


def get_image_files(input_dir, pattern="*", limit=None):
    """Get all image files from input directory."""
    input_path = Path(input_dir)
    if not input_path.exists():
        print(f"Error: Input directory '{input_dir}' does not exist.")
        print(f"Please create it and add your images: mkdir {input_dir}")
        sys.exit(1)

    image_files = []
    for file in input_path.iterdir():
        if file.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        if pattern != "*" and not file.match(pattern):
            continue
        image_files.append(file)

    sorted_files = sorted(image_files)

    # Apply limit if specified
    if limit and limit > 0:
        sorted_files = sorted_files[:limit]

    return sorted_files


def ensure_output_dir(output_dir):
    """Create output directory if it doesn't exist."""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    return output_path


def log_error(error_log_path, filename, error_message):
    """Log errors to error log file."""
    with open(error_log_path, "a") as f:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {filename}: {error_message}\n")


def process_images(image_files, output_path, error_log_path, args):
    """Process all images with background removal."""
    total_images = len(image_files)

    if total_images == 0:
        if not args.quiet:
            print("No images found matching criteria.")
            print(f"Supported formats: {', '.join(IMAGE_EXTENSIONS)}")
        return

    # Filter out existing files if skip_existing is enabled
    if args.skip_existing:
        original_count = total_images
        image_files = [
            f for f in image_files if not (output_path / (f.stem + ".png")).exists()
        ]
        total_images = len(image_files)
        if not args.quiet and original_count != total_images:
            print(f"Skipping {original_count - total_images} existing files")

    if total_images == 0:
        if not args.quiet:
            print("All images already processed. Remove --skip-existing to reprocess.")
        return

    if not args.quiet:
        print(f"\n{'=' * 60}")
        print("batch-rembg")
        print(f"{'=' * 60}")
        print(f"Total images to process: {total_images}")
        print(f"Input directory: {args.input}")
        print(f"Output directory: {args.output}")
        print(f"Model: {args.model}")
        if args.limit:
            print(f"Limit: Processing first {args.limit} images")
        print(f"{'=' * 60}\n")

    # Dry run mode - just list files
    if args.dry_run:
        print("DRY RUN MODE - No files will be processed\n")
        print("Files that would be processed:")
        for idx, img_file in enumerate(image_files, 1):
            output_filename = img_file.stem + ".png"
            print(f"  [{idx}] {img_file.name} → {output_filename}")
        print(f"\nTotal: {total_images} files")
        return

    # Create session once for all images (critical for performance)
    if not args.quiet:
        print(f"Loading {args.model} model...")
    session = new_session(model_name=args.model)
    if not args.quiet:
        print("Model loaded successfully!\n")

    # Statistics
    processed = 0
    failed = 0
    start_time = time.time()

    # Process each image
    for idx, image_file in enumerate(image_files, 1):
        try:
            # Generate output filename
            output_filename = image_file.stem + ".png"
            output_file = output_path / output_filename

            # Open and process image
            with open(image_file, "rb") as input_file:
                input_data = input_file.read()

            # Remove background
            output_data = remove(
                input_data,
                session=session,
                alpha_matting=args.alpha_matting,
                alpha_matting_foreground_threshold=args.fg_threshold,
                alpha_matting_background_threshold=args.bg_threshold,
                post_process_mask=args.post_process,
            )

            # Save as PNG
            with open(output_file, "wb") as output_file_handle:
                output_file_handle.write(output_data)

            processed += 1

            # Progress update
            if not args.quiet:
                elapsed = time.time() - start_time
                images_per_sec = processed / elapsed if elapsed > 0 else 0
                remaining = total_images - processed
                eta_seconds = remaining / images_per_sec if images_per_sec > 0 else 0
                progress_percent = (idx / total_images) * 100
                print(
                    f"[{idx}/{total_images}] ({progress_percent:.1f}%) "
                    f"{image_file.name} → {output_filename} "
                    f"| Speed: {images_per_sec:.2f} img/s "
                    f"| ETA: {format_time(eta_seconds)}"
                )

        except Exception as e:
            failed += 1
            error_msg = f"{type(e).__name__}: {str(e)}"
            if not args.quiet:
                print(f"[ERROR] Failed to process {image_file.name}: {error_msg}")
            log_error(error_log_path, image_file.name, error_msg)

    # Final summary
    total_time = time.time() - start_time
    if not args.quiet:
        print(f"\n{'=' * 60}")
        print("Processing Complete!")
        print(f"{'=' * 60}")
        print(f"Total images: {total_images}")
        print(f"Successfully processed: {processed}")
        print(f"Failed: {failed}")
        print(f"Total time: {format_time(total_time)}")
        if total_time > 0:
            print(f"Average speed: {processed / total_time:.2f} images/second")

        if failed > 0:
            print(f"\nErrors logged to: {error_log_path}")

        print(f"\nOutput files saved to: {args.output}/")
        print(f"{'=' * 60}\n")
    else:
        # Quiet mode: just print essential stats
        print(
            f"Processed: {processed}, Failed: {failed}, Time: {format_time(total_time)}"
        )


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="batch-rembg: Batch background removal using RemBG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage (uses input/ and output/ folders)
  %(prog)s

  # Custom input/output paths
  %(prog)s --input /path/to/images --output /path/to/results

  # Use faster model
  %(prog)s --model u2netp

  # Test on first 10 images
  %(prog)s --limit 10

  # Resume processing (skip already processed)
  %(prog)s --skip-existing

  # Preview what will be processed
  %(prog)s --dry-run

  # Quiet mode for automation
  %(prog)s --quiet

Available models:
"""
        + "\n".join(f"  {name:20} {desc}" for name, desc in MODELS.items()),
    )

    parser.add_argument(
        "-i",
        "--input",
        default=DEFAULT_INPUT_DIR,
        help=f"Input directory containing images (default: {DEFAULT_INPUT_DIR})",
    )

    parser.add_argument(
        "-o",
        "--output",
        default=DEFAULT_OUTPUT_DIR,
        help=f"Output directory for processed images (default: {DEFAULT_OUTPUT_DIR})",
    )

    parser.add_argument(
        "-m",
        "--model",
        default=DEFAULT_MODEL,
        choices=list(MODELS.keys()),
        help=f"AI model to use (default: {DEFAULT_MODEL})",
    )

    parser.add_argument(
        "-l",
        "--limit",
        type=int,
        metavar="N",
        help="Process only first N images (useful for testing)",
    )

    parser.add_argument(
        "-p",
        "--pattern",
        default="*",
        help="Filename pattern to match (default: * for all)",
    )

    parser.add_argument(
        "-s",
        "--skip-existing",
        action="store_true",
        help="Skip images that already have output files (resume capability)",
    )

    parser.add_argument(
        "-d",
        "--dry-run",
        action="store_true",
        help="Show what would be processed without actually processing",
    )

    parser.add_argument(
        "-q", "--quiet", action="store_true", help="Minimal output (only final summary)"
    )

    parser.add_argument(
        "-a",
        "--alpha-matting",
        action="store_true",
        help="Enable alpha matting for better edges on complex objects",
    )

    parser.add_argument(
        "--fg-threshold",
        type=int,
        default=240,
        metavar="N",
        help="Alpha matting foreground threshold (default: 240)",
    )

    parser.add_argument(
        "--bg-threshold",
        type=int,
        default=10,
        metavar="N",
        help="Alpha matting background threshold (default: 10)",
    )

    parser.add_argument(
        "--post-process",
        action="store_true",
        help="Post-process mask for cleaner edges",
    )

    parser.add_argument(
        "--error-log",
        default=DEFAULT_ERROR_LOG,
        help=f"Error log file path (default: {DEFAULT_ERROR_LOG})",
    )

    parser.add_argument(
        "--list-models", action="store_true", help="List available models and exit"
    )

    return parser.parse_args()


def main():
    """Main execution function."""
    args = parse_arguments()

    # Handle --list-models
    if args.list_models:
        print("Available models:\n")
        for name, desc in MODELS.items():
            print(f"  {name:20} {desc}")
        sys.exit(0)

    try:
        # Get input images
        image_files = get_image_files(args.input, args.pattern, args.limit)

        # Ensure output directory exists
        output_path = ensure_output_dir(args.output)

        # Process images
        process_images(image_files, output_path, args.error_log, args)

    except KeyboardInterrupt:
        if not args.quiet:
            print("\n\nProcessing interrupted by user. Exiting gracefully...")
        sys.exit(0)
    except Exception as e:
        if not args.quiet:
            print(f"\n\nFatal error: {type(e).__name__}: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
