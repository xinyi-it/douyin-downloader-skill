---
name: douyin-downloader
description: "Download Douyin (抖音) videos without watermark. Use when user wants to: (1) download Douyin videos, (2) get video info (title, author, stats). Supports short links (v.douyin.com), full URLs, and share text with embedded links."
---

# Douyin Downloader Skill

Download Douyin (抖音) videos without watermark. Zero browser dependency — pure Python + requests.

## Setup (One-Time)

```bash
git clone https://github.com/xinyi-it/douyin-downloader.git ~/douyin-downloader
cd ~/douyin-downloader && pip install -r requirements.txt
mkdir -p ~/Documents/douyin_videos
```

## Usage

### Download Video

```bash
python ~/douyin-downloader/douyin.py "https://v.douyin.com/xxx/"
python ~/douyin-downloader/douyin.py "https://www.douyin.com/video/123456" -o ./videos
python ~/douyin-downloader/douyin.py "https://v.douyin.com/xxx/" --hd
```

### Info Only (No Download)

```bash
python ~/douyin-downloader/douyin.py "https://v.douyin.com/xxx/" --info
python ~/douyin-downloader/douyin.py "https://v.douyin.com/xxx/" --info --json
```

### From Share Text

```bash
python ~/douyin-downloader/douyin.py "7.43 FuL:/ 描述文字 https://v.douyin.com/xxx/ 复制此链接"
```

## Supported URL Formats

- Short link: `https://v.douyin.com/xxxxxxx/`
- Full URL: `https://www.douyin.com/video/1234567890`
- Share text: `7.43 FuL:/ 描述 https://v.douyin.com/xxx/ 复制此链接...`

## Output

- Default directory: `~/Documents/douyin_videos/`
- Filename: `{video_id}.mp4`
- No watermark

## Troubleshooting

- **"无法从文本中提取抖音链接"**: User may have pasted incomplete text. Ask for the full share link.
- **Short link redirects to homepage**: Link expired. Ask user to re-share from the app.
- **Download fails with 403**: Video may be region-restricted or deleted.

## How It Works

1. Parse short link → get video ID via HTTP redirect
2. Fetch `iesdouyin.com/share/video/{id}/` with mobile UA
3. Extract `play_addr` from HTML, replace `/playwm/` with `/play/` (removes watermark)
4. Download video with proper headers

No browser, no cookies, no Selenium — just `requests`.
