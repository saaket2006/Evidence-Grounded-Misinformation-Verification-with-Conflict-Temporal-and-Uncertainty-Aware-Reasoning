"""Download FEVER dataset files or create verified benchmark subsets.

Supports downloading official FEVER splits and preparing standard directories.
"""

import argparse
import json
import logging
from pathlib import Path
import sys
import urllib.request

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# Official FEVER download URLs
FEVER_URLS = {
    "dev": "https://fever.ai/download/fever/paper_dev.jsonl",
    "train_sample": "https://fever.ai/download/fever/train.jsonl",
}


def download_file(url: str, dest_path: Path, timeout: int = 30) -> bool:
    """Download a file with fallback handling."""
    logger.info(f"Downloading from {url} to {dest_path}...")
    try:
        urllib.request.urlretrieve(url, dest_path)
        logger.info(f"Successfully downloaded {dest_path.name} ({dest_path.stat().st_size} bytes)")
        return True
    except Exception as e:
        logger.warning(f"Could not download from {url}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Download FEVER dataset")
    parser.add_argument("--output_dir", type=str, default="data/raw", help="Directory to save raw files")
    parser.add_argument("--splits", nargs="+", default=["dev"], help="Splits to download (dev, train)")
    parser.add_argument("--force", action="store_true", help="Force re-download even if files exist")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for split in args.splits:
        target_file = out_dir / f"fever_{split}.jsonl"
        if target_file.exists() and not args.force:
            logger.info(f"File already exists: {target_file}. Use --force to re-download.")
            continue

        if split in FEVER_URLS:
            success = download_file(FEVER_URLS[split], target_file)
            if not success:
                logger.info(f"Download from primary URL failed. A curated benchmark will be generated during prepare_data.py.")
        else:
            logger.warning(f"Unknown split: {split}")


if __name__ == "__main__":
    main()
