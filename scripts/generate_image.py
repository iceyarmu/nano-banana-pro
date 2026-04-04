#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "httpx>=0.27.0",
# ]
# ///
"""
Generate images using Gemini Flash Image API via direct HTTP requests.

Usage:
    uv run generate_image.py --prompt "description" --filename "output.png" \
        [--input-image img1.png ...] [--resolution 1K|2K|4K] \
        [--aspect-ratio 1:1|16:9|9:16|4:3|3:4]
"""

import argparse
import base64
import mimetypes
import os
import struct
import sys
from pathlib import Path

RATIO_TO_MODEL = {
    "16:9": "landscape",
    "9:16": "portrait",
    "1:1": "square",
    "4:3": "four-three",
    "3:4": "three-four",
}

RESOLUTION_TO_SUFFIX = {
    "1K": "",
    "2K": "-2k",
    "4K": "-4k",
}


def build_model_name(aspect_ratio: str, resolution: str) -> str:
    ratio_part = RATIO_TO_MODEL[aspect_ratio]
    res_suffix = RESOLUTION_TO_SUFFIX[resolution]
    return f"gemini-3.1-flash-image-{ratio_part}{res_suffix}"


def image_to_part(img_path: str) -> dict:
    """Read image file and return as inlineData part for Gemini API."""
    path = Path(img_path)
    if not path.exists():
        print(f"Error: Image not found: {img_path}", file=sys.stderr)
        sys.exit(1)
    mime_type = mimetypes.guess_type(str(path))[0] or "image/png"
    data = base64.b64encode(path.read_bytes()).decode()
    return {"inlineData": {"mimeType": mime_type, "data": data}}


def get_image_max_dim(img_path: str) -> int:
    """Get max dimension of an image from file header (PNG/JPEG only)."""
    try:
        with open(img_path, "rb") as f:
            header = f.read(32)
            # PNG
            if header[:8] == b"\x89PNG\r\n\x1a\n":
                w, h = struct.unpack(">II", header[16:24])
                return max(w, h)
            # JPEG
            if header[:2] == b"\xff\xd8":
                f.seek(2)
                while True:
                    marker = f.read(2)
                    if len(marker) < 2:
                        break
                    size_bytes = f.read(2)
                    if len(size_bytes) < 2:
                        break
                    size = struct.unpack(">H", size_bytes)[0]
                    m = struct.unpack(">H", marker)[0]
                    if 0xFFC0 <= m <= 0xFFC3:
                        f.read(1)
                        h, w = struct.unpack(">HH", f.read(4))
                        return max(w, h)
                    f.read(size - 2)
    except Exception:
        pass
    return 0


def main():
    parser = argparse.ArgumentParser(description="Generate images via Gemini Flash Image API")
    parser.add_argument("--prompt", "-p", required=True, help="Image description/prompt")
    parser.add_argument("--filename", "-f", required=True, help="Output filename")
    parser.add_argument("--input-image", "-i", nargs="+", help="Input image path(s) for editing")
    parser.add_argument("--resolution", "-r", choices=["1K", "2K", "4K"], default="1K",
                        help="Output resolution (default: 1K)")
    parser.add_argument("--aspect-ratio", "-a", choices=["1:1", "16:9", "9:16", "4:3", "3:4"],
                        default="16:9", help="Aspect ratio (default: 16:9)")
    parser.add_argument("--api-key", "-k", help="API key (overrides GEMINI_API_KEY env)")
    parser.add_argument("--base-url", "-b", help="Base URL (overrides GEMINI_BASE_URL env)")
    args = parser.parse_args()

    api_key = args.api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: No API key. Set GEMINI_API_KEY or use --api-key.", file=sys.stderr)
        sys.exit(1)

    base_url = args.base_url or os.environ.get("GEMINI_BASE_URL") or "https://generativelanguage.googleapis.com"
    base_url = base_url.rstrip("/")

    output_path = Path(args.filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Build request parts
    parts = []
    output_resolution = args.resolution

    if args.input_image:
        max_dim = 0
        for img_path in args.input_image:
            parts.append(image_to_part(img_path))
            dim = get_image_max_dim(img_path)
            max_dim = max(max_dim, dim)
            print(f"Loaded input image: {img_path}")

        # Auto-detect resolution from input dimensions
        if args.resolution == "1K" and max_dim > 0:
            if max_dim >= 3000:
                output_resolution = "4K"
            elif max_dim >= 1500:
                output_resolution = "2K"
            print(f"Auto-detected resolution: {output_resolution} (max input dim {max_dim})")

    parts.append({"text": args.prompt})

    model_name = build_model_name(args.aspect_ratio, output_resolution)
    print(f"Using model: {model_name}")

    url = f"{base_url}/v1beta/models/{model_name}:generateContent"

    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {
            "responseModalities": ["TEXT", "IMAGE"],
        },
    }

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }

    import httpx

    try:
        with httpx.Client(timeout=300) as client:
            print(f"Requesting {url} ...")
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            result = resp.json()
    except httpx.HTTPStatusError as e:
        print(f"API error {e.response.status_code}: {e.response.text}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Request error: {e}", file=sys.stderr)
        sys.exit(1)

    # Process response
    candidates = result.get("candidates", [])
    if not candidates:
        print(f"Error: No candidates in response. Full response:\n{result}", file=sys.stderr)
        sys.exit(1)

    resp_parts = candidates[0].get("content", {}).get("parts", [])
    image_saved = False

    for part in resp_parts:
        if "text" in part:
            print(f"Model response: {part['text']}")
        elif "inlineData" in part or "inline_data" in part:
            # base64 image data
            inline = part.get("inlineData") or part.get("inline_data")
            image_data = base64.b64decode(inline["data"])
            output_path.write_bytes(image_data)
            image_saved = True
        elif "fileData" in part or "file_data" in part:
            # URL-based image response
            file_info = part.get("fileData") or part.get("file_data")
            file_uri = file_info.get("fileUri") or file_info.get("file_uri")
            if file_uri:
                print(f"Downloading image from: {file_uri}")
                with httpx.Client(timeout=120) as dl_client:
                    img_resp = dl_client.get(file_uri)
                    img_resp.raise_for_status()
                    output_path.write_bytes(img_resp.content)
                image_saved = True

    if image_saved:
        print(f"\nImage saved: {output_path.resolve()}")
    else:
        print("Error: No image in response.", file=sys.stderr)
        print(f"Response parts: {resp_parts}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
