---
name: nano-banana-pro
description: Generate/edit images with Nano Banana Pro (Gemini Flash Image). Use for image create/modify requests incl. edits. Supports text-to-image + image-to-image (single or multiple reference images); 1K/2K/4K; aspect ratios 1:1/16:9/9:16/4:3/3:4; use --input-image.
---

# Nano Banana Pro Image Generation & Editing

Generate new images or edit existing ones using the Gemini Flash Image API (via GEMINI_BASE_URL proxy).

## Usage

Run the script using absolute path (do NOT cd to skill directory first):

**Generate new image:**
```bash
uv run ~/.openclaw/workspace/skills/nano-banana-pro/scripts/generate_image.py --prompt "your image description" --filename "output-name.png" [--resolution 1K|2K|4K] [--aspect-ratio 1:1|16:9|9:16|4:3|3:4]
```

**Edit existing image (single reference):**
```bash
uv run ~/.openclaw/workspace/skills/nano-banana-pro/scripts/generate_image.py --prompt "editing instructions" --filename "output-name.png" --input-image "path/to/input.png" [--resolution 1K|2K|4K] [--aspect-ratio 1:1|16:9|9:16|4:3|3:4]
```

**Edit with multiple reference images:**
```bash
uv run ~/.openclaw/workspace/skills/nano-banana-pro/scripts/generate_image.py --prompt "combine these styles" --filename "output-name.png" --input-image "ref1.png" "ref2.png" "ref3.png" [--resolution 1K|2K|4K] [--aspect-ratio 1:1|16:9|9:16|4:3|3:4]
```

**Important:** Always run from the user's current working directory so images are saved where the user is working, not in the skill directory.

## Default Workflow (draft → iterate → final)

Goal: fast iteration without burning time on 4K until the prompt is correct.

- Draft (1K): quick feedback loop
  - `uv run ~/.openclaw/workspace/skills/nano-banana-pro/scripts/generate_image.py --prompt "<draft prompt>" --filename "yyyy-mm-dd-hh-mm-ss-draft.png" --resolution 1K [--aspect-ratio 16:9]`
- Iterate: adjust prompt in small diffs; keep filename new per run
  - If editing: keep the same `--input-image` for every iteration until you're happy.
- Final (4K): only when prompt is locked
  - `uv run ~/.openclaw/workspace/skills/nano-banana-pro/scripts/generate_image.py --prompt "<final prompt>" --filename "yyyy-mm-dd-hh-mm-ss-final.png" --resolution 4K [--aspect-ratio 16:9]`

## Resolution Options

The API supports three resolutions (uppercase K required):

- **1K** (default) - ~1024px resolution
- **2K** - ~2048px resolution
- **4K** - ~4096px resolution

Map user requests to API parameters:
- No mention of resolution, Default → `4K`
- "low resolution", "1080", "1080p", "1K" → `1K`
- "2K", "2048", "normal", "medium resolution" → `2K`
- "high resolution", "high-res", "hi-res", "4K", "ultra" → `4K`

## Aspect Ratio Options

Supported aspect ratios (default: `16:9`):

- **1:1** - Square
- **16:9** - Widescreen landscape (default)
- **9:16** - Vertical/portrait (stories, reels)
- **4:3** - Classic landscape
- **3:4** - Classic portrait

Map user requests to API parameters:
- No mention of aspect ratio, Default → `16:9`
- "square", "1:1" → `1:1`
- "widescreen", "landscape", "16:9", "banner", "desktop wallpaper" → `16:9`
- "vertical", "portrait", "story", "reel", "9:16", "phone wallpaper" → `9:16`
- "4:3", "classic", "standard" → `4:3`
- "3:4", "classic portrait" → `3:4`

## Model

Default model: `gemini-3.1-flash-image`

The script uses `GEMINI_BASE_URL` environment variable to route requests through a proxy. No API key required when using the proxy.

## Preflight + Common Failures (fast fixes)

- Preflight:
  - `command -v uv` (must exist)
  - If editing: verify all `--input-image` paths exist (`test -f` each)

- Common failures:
  - `Error loading input image:` → wrong path / unreadable file; verify `--input-image` points to a real image
  - "502 Bad Gateway" → proxy service may be down; check `GEMINI_BASE_URL` is reachable

## Filename Generation

Generate filenames with the pattern: `yyyy-mm-dd-hh-mm-ss-name.png`

**Format:** `{timestamp}-{descriptive-name}.png`
- Timestamp: Current date/time in format `yyyy-mm-dd-hh-mm-ss` (24-hour format)
- Name: Descriptive lowercase text with hyphens
- Keep the descriptive part concise (1-5 words typically)
- Use context from user's prompt or conversation
- If unclear, use random identifier (e.g., `x9k2`, `a7b3`)

Examples:
- Prompt "A serene Japanese garden" → `2025-11-23-14-23-05-japanese-garden.png`
- Prompt "sunset over mountains" → `2025-11-23-15-30-12-sunset-mountains.png`
- Prompt "create an image of a robot" → `2025-11-23-16-45-33-robot.png`
- Unclear context → `2025-11-23-17-12-48-x9k2.png`

## Image Editing

When the user wants to modify an existing image:
1. Check if they provide image path(s) or reference image(s) in the current directory
2. Use `--input-image` parameter with one or more image paths (e.g., `--input-image img1.png img2.png`)
3. The prompt should contain editing instructions (e.g., "make the sky more dramatic", "remove the person", "change to cartoon style")
4. Multiple reference images are useful for style transfer, combining elements, or providing context
5. Common editing tasks: add/remove elements, change style, adjust colors, blur background, etc.

## Prompt Handling

**For generation:** Pass user's image description as-is to `--prompt`. Only rework if clearly insufficient.

**For editing:** Pass editing instructions in `--prompt` (e.g., "add a rainbow in the sky", "make it look like a watercolor painting")

Preserve user's creative intent in both cases.

**Language rule:** Always write prompt descriptions in English (scene, style, composition, lighting, etc.). Chinese is only allowed for in-image text content such as dialogue bubbles, titles, labels, or captions that should appear literally in the generated image — and must be wrapped in single quotes (e.g., `with a speech bubble saying '你好世界'`).

## Prompt Templates (high hit-rate)

Use templates when the user is vague or when edits must be precise.

- Generation template:
  - "Create an image of: <subject>. Style: <style>. Composition: <camera/shot>. Lighting: <lighting>. Background: <background>. Color palette: <palette>. Avoid: <list>."

- Editing template (preserve everything else):
  - "Change ONLY: <single change>. Keep identical: subject, composition/crop, pose, lighting, color palette, background, text, and overall style. Do not add new objects. If text exists, keep it unchanged."

## Output

- Saves PNG to current directory (or specified path if filename includes directory)
- Script outputs the full path to the generated image
- **Do not read the image back** - just inform the user of the saved path

## Examples

**Generate new image:**
```bash
uv run ~/.openclaw/workspace/skills/nano-banana-pro/scripts/generate_image.py --prompt "A serene Japanese garden with cherry blossoms" --filename "2025-11-23-14-23-05-japanese-garden.png" --resolution 4K --aspect-ratio 16:9
```

**Generate vertical image (e.g., phone wallpaper):**
```bash
uv run ~/.openclaw/workspace/skills/nano-banana-pro/scripts/generate_image.py --prompt "A tall waterfall in a misty forest" --filename "2025-11-23-14-24-00-waterfall.png" --resolution 4K --aspect-ratio 9:16
```

**Edit existing image:**
```bash
uv run ~/.openclaw/workspace/skills/nano-banana-pro/scripts/generate_image.py --prompt "make the sky more dramatic with storm clouds" --filename "2025-11-23-14-25-30-dramatic-sky.png" --input-image "original-photo.jpg" --resolution 4K --aspect-ratio 16:9
```

**Multiple reference images:**
```bash
uv run ~/.openclaw/workspace/skills/nano-banana-pro/scripts/generate_image.py --prompt "combine the composition of the first image with the color palette of the second" --filename "2025-11-23-14-30-00-combined-style.png" --input-image "composition-ref.png" "color-ref.png" --resolution 4K
```
