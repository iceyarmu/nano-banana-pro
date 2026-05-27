#!/usr/bin/env python3
"""
Generate images via the async image generation API.

Submits a task and polls until completion, then downloads the resulting image.

Requires: httpx (pip install httpx)

Usage:
    python3 generate_image.py --prompt "description" --filename "output.png" \
        [--input-image img1.png ...] [--resolution 1K|2K|4K] \
        [--aspect-ratio 1:1|16:9|9:16|4:3|3:4]
"""

import argparse
import base64
import mimetypes
import os
import sys
import time
from pathlib import Path

API_KEY = os.environ.get("IMAGE_API_KEY") or "iceyarmu"
BASE_URL = os.environ.get("IMAGE_API_BASE") or "http://127.0.0.1:8000"
MODEL = "nana-banana-2"

POLL_INTERVAL_SECONDS = 3
POLL_TIMEOUT_SECONDS = 600


def image_to_data_url(img_path: str) -> str:
    """Read image file and return as a data: URL."""
    path = Path(img_path)
    if not path.exists():
        print(f"Error: Image not found: {img_path}", file=sys.stderr)
        sys.exit(1)
    mime_type = mimetypes.guess_type(str(path))[0] or "image/png"
    data = base64.b64encode(path.read_bytes()).decode()
    return f"data:{mime_type};base64,{data}"


def main():
    parser = argparse.ArgumentParser(description="Generate images via async image generation API")
    parser.add_argument("--prompt", "-p", required=True, help="Image description/prompt")
    parser.add_argument("--filename", "-f", required=True, help="Output filename")
    parser.add_argument("--input-image", "-i", nargs="+", help="Input image path(s) for editing")
    parser.add_argument("--resolution", "-r", choices=["1K", "2K", "4K"], default="1K",
                        help="Output resolution (default: 1K)")
    parser.add_argument("--aspect-ratio", "-a", choices=["1:1", "16:9", "9:16", "4:3", "3:4"],
                        default="16:9", help="Aspect ratio (default: 16:9)")
    args = parser.parse_args()

    api_key = API_KEY
    base_url = BASE_URL.rstrip("/")

    output_path = Path(args.filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "model": MODEL,
        "prompt": args.prompt,
        "aspect_ratio": args.aspect_ratio,
        "resolution": args.resolution,
    }

    if args.input_image:
        images = []
        for img_path in args.input_image:
            images.append(image_to_data_url(img_path))
            print(f"Loaded input image: {img_path}")
        payload["images"] = images

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    submit_url = f"{base_url}/v1/videos"

    import httpx

    try:
        with httpx.Client(timeout=300) as client:
            print(f"Submitting task to {submit_url} ...")
            resp = client.post(submit_url, json=payload, headers=headers)
            resp.raise_for_status()
            task = resp.json()
    except httpx.HTTPStatusError as e:
        print(f"API error {e.response.status_code}: {e.response.text}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Request error: {e}", file=sys.stderr)
        sys.exit(1)

    task_id = task.get("task_id") or task.get("id")
    if not task_id:
        print(f"Error: No task_id in response: {task}", file=sys.stderr)
        sys.exit(1)

    print(f"Task submitted: {task_id} (status: {task.get('status')})")

    # Poll for completion
    poll_url = f"{base_url}/v1/videos/{task_id}"
    poll_headers = {"Authorization": f"Bearer {api_key}"}
    deadline = time.monotonic() + POLL_TIMEOUT_SECONDS
    last_progress = -1

    try:
        with httpx.Client(timeout=60) as client:
            while True:
                if time.monotonic() > deadline:
                    print(f"Error: Task timed out after {POLL_TIMEOUT_SECONDS}s", file=sys.stderr)
                    sys.exit(1)
                time.sleep(POLL_INTERVAL_SECONDS)
                resp = client.get(poll_url, headers=poll_headers)
                resp.raise_for_status()
                task = resp.json()
                status = task.get("status")
                progress = task.get("progress", 0)
                if progress != last_progress:
                    print(f"Status: {status}, progress: {progress}%")
                    last_progress = progress
                if status == "completed":
                    break
                if status == "failed":
                    err = task.get("error") or {}
                    print(f"Error: Task failed: {err.get('message')} (code: {err.get('code')})", file=sys.stderr)
                    sys.exit(1)
    except httpx.HTTPStatusError as e:
        print(f"Poll error {e.response.status_code}: {e.response.text}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Poll error: {e}", file=sys.stderr)
        sys.exit(1)

    # Extract image URL from completed task
    result_urls = (task.get("metadata") or {}).get("result_urls") or []
    image_url = task.get("image_url") or task.get("url") or (result_urls[0] if result_urls else None)
    if not image_url:
        print(f"Error: No image URL in completed task: {task}", file=sys.stderr)
        sys.exit(1)

    if image_url.startswith("data:"):
        try:
            header, _, b64data = image_url.partition(",")
            if ";base64" not in header:
                print(f"Error: Unsupported data URL encoding: {header}", file=sys.stderr)
                sys.exit(1)
            print(f"Decoding inline data URL ({header})")
            output_path.write_bytes(base64.b64decode(b64data))
        except Exception as e:
            print(f"Decode error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Downloading image from: {image_url}")
        try:
            with httpx.Client(timeout=120) as client:
                img_resp = client.get(image_url)
                img_resp.raise_for_status()
                output_path.write_bytes(img_resp.content)
        except Exception as e:
            print(f"Download error: {e}", file=sys.stderr)
            sys.exit(1)

    print(f"\nImage saved: {output_path.resolve()}")


if __name__ == "__main__":
    main()
