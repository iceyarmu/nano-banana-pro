---
name: nano-banana-pro
description: Generate/edit images via Gemini Flash Image API. Supports text-to-image and image editing (single/multi reference). Aspect ratio and resolution controlled via model name.
---

# Nano Banana Pro

Generate or edit images via Gemini Flash Image API (`GEMINI_BASE_URL` proxy).

## Command

```bash
uv run ~/.openclaw/workspace/skills/nano-banana-pro/scripts/generate_image.py \
  --prompt "description" --filename "output.png" \
  [--input-image img1.png ...] \
  [--resolution 1K|2K|4K] [--aspect-ratio 1:1|16:9|9:16|4:3|3:4]
```

Always run from user's working directory, do NOT cd to skill directory.

## Model Naming Convention

Aspect ratio and resolution are controlled via model name, not config params.

**Format:** `gemini-3.1-flash-image-{ratio}[-{resolution}]`

| Aspect Ratio | Model Suffix |
|---|---|
| 16:9 横屏 | `landscape` |
| 9:16 竖屏 | `portrait` |
| 1:1 方图 | `square` |
| 4:3 横屏 | `four-three` |
| 3:4 竖屏 | `three-four` |

| Resolution | Model Suffix |
|---|---|
| 1K (~1024px) | *(无后缀)* |
| 2K (~2048px) | `-2k` |
| 4K (~4096px) | `-4k` |

**示例:**
- `gemini-3.1-flash-image-landscape` → 16:9, 1K
- `gemini-3.1-flash-image-square-2k` → 1:1, 2K
- `gemini-3.1-flash-image-portrait-4k` → 9:16, 4K
- `gemini-3.1-flash-image-four-three-4k` → 4:3, 4K

脚本会根据 `--aspect-ratio` 和 `--resolution` 自动拼接模型名。

## Defaults

- **Resolution:** 4K（用户未指定时）
- **Aspect Ratio:** 16:9 landscape（用户未指定时）
- **Editing:** 自动根据输入图片尺寸推断分辨率

## Filename

Pattern: `yyyy-mm-dd-hh-mm-ss-descriptive-name.png`

从 prompt 提取简短描述（1-5 词，小写，连字符），不确定时用随机 ID（如 `x9k2`）。

## Prompt Rules

- 始终用英文写 prompt
- 中文仅用于图中文字内容（对话气泡、标题等），用单引号包裹：`with text saying '你好'`
- 生成：直接传用户描述，仅在明显不足时润色
- 编辑：传编辑指令（如 "add rainbow to sky"）

精确编辑模板：
> "Change ONLY: \<change\>. Keep identical: subject, composition, pose, lighting, color palette, background, text, and style."

## Editing

用 `--input-image` 传入一个或多个图片路径，prompt 写编辑指令。

## Preflight

- `command -v uv`（必须安装）
- 编辑时：验证所有 `--input-image` 路径存在

## Output

- 保存 PNG 到当前目录
- 不要回读图片，将图片发送到飞书即可
