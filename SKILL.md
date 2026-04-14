---
name: nano-banana-pro
description: Generate or edit images via Gemini Flash Image. Supports text-to-image and image editing (single or multi reference) with aspect ratio and resolution control.
---

# Nano Banana Pro

Generate or edit images via Gemini Flash Image.

## Command

```bash
python3 ~/.openclaw/workspace/skills/nano-banana-pro/scripts/generate_image.py \
  --prompt "description" --filename "output.png" \
  [--input-image img1.png ...] \
  [--resolution 1K|2K|4K] [--aspect-ratio 1:1|16:9|9:16|4:3|3:4]
```

Always run from user's working directory, do NOT cd to skill directory.

## Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--prompt` / `-p` | Yes | - | Image description or edit instruction |
| `--filename` / `-f` | Yes | - | Output file path (.png) |
| `--input-image` / `-i` | No | - | Input image path(s) for editing; pass one or more |
| `--resolution` / `-r` | No | `1K` | `1K`, `2K`, or `4K` |
| `--aspect-ratio` / `-a` | No | `16:9` | `1:1`, `16:9`, `9:16`, `4:3`, or `3:4` |

Recommended defaults when the user does not specify: `--resolution 2K`, `--aspect-ratio 16:9`.

## Filename

Pattern: `yyyy-mm-dd-hh-mm-ss-descriptive-name.png`

从 prompt 提取简短描述（1-5 词，小写，连字符），不确定时用随机 ID（如 `x9k2`）。

## Prompt Rules

- 始终用英文写 prompt
- 图中文字内容（对话气泡、标题等）可以用中文，用单引号包裹：`with text saying '你好'`
- 生成：直接传用户描述，仅在明显不足时润色
- 编辑：传编辑指令（如 "add rainbow to sky"）

精确编辑模板：
> "Change ONLY: \<change\>. Keep identical: subject, composition, pose, lighting, color palette, background, text, and style."

## Editing

用 `--input-image` 传入一个或多个图片路径，prompt 写编辑指令。

## Preflight

- `command -v python3`（必须安装）
- `python3 -c "import httpx"`（httpx 必须已安装）
- 编辑时：验证所有 `--input-image` 路径存在

## Output

- 保存 PNG 到当前目录
- 不要回读图片，将图片发送到飞书即可
