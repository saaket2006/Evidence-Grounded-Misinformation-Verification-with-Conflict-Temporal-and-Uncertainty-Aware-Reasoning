"""Helper to download model files with resume support and progress logging."""

import os
import sys
import time
import urllib.request


def download_with_progress(url: str, output_path: str) -> None:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    existing_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        total_size = int(resp.headers.get("Content-Length", 0))

    if existing_size >= total_size and total_size > 0:
        print(f"{os.path.basename(output_path)} already fully downloaded ({existing_size} bytes).")
        return

    print(f"Downloading {os.path.basename(output_path)} ({total_size / (1024*1024):.1f} MB)...")
    if existing_size > 0:
        headers["Range"] = f"bytes={existing_size}-"

    req = urllib.request.Request(url, headers=headers)
    mode = "ab" if existing_size > 0 else "wb"
    t0 = time.time()
    last_log = t0
    downloaded = existing_size

    with urllib.request.urlopen(req) as resp, open(output_path, mode) as fp:
        while True:
            chunk = resp.read(1024 * 512)  # 512 KB
            if not chunk:
                break
            fp.write(chunk)
            downloaded += len(chunk)
            now = time.time()
            if now - last_log > 2.0:
                speed = (downloaded - existing_size) / (1024 * 1024 * max(0.1, now - t0))
                pct = (downloaded / total_size * 100) if total_size else 0
                print(f"Progress: {downloaded / (1024*1024):.1f}/{total_size / (1024*1024):.1f} MB ({pct:.1f}%) @ {speed:.2f} MB/s")
                last_log = now

    print(f"Finished {os.path.basename(output_path)} in {time.time()-t0:.1f}s.")


def main():
    model_id = "typeform/distilbert-base-uncased-mnli"
    dest_dir = "models/distilbert-base-uncased-mnli"
    files = ["config.json", "vocab.txt", "tokenizer_config.json", "special_tokens_map.json", "model.safetensors"]
    base_url = f"https://huggingface.co/{model_id}/resolve/main/"

    for f in files:
        download_with_progress(base_url + f, os.path.join(dest_dir, f))


if __name__ == "__main__":
    main()
