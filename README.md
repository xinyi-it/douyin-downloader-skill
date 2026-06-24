# douyin-downloader

抖音无水印视频下载器 — AI Agent 技能包

零浏览器依赖，纯 Python + requests，适配 Hermes / Claude Code / OpenClaw 等 AI Agent。

## ✨ 特点

- **无水印**：把 `/playwm/` 替换为 `/play/`，去掉抖音水印
- **零依赖**：只需 `requests`，不需要 Chrome / Selenium / yt-dlp
- **多格式**：支持短链接、完整URL、分享文本
- **AI 友好**：自带 SKILL.md，AI Agent 直接识别调用
- **JSON 输出**：`--info --json` 方便 Agent 解析

## 安装

```bash
git clone https://github.com/xinyi-it/douyin-downloader-skill.git
cd douyin-downloader
pip install -r requirements.txt
```

## 使用

### 下载视频

```bash
python douyin.py https://v.douyin.com/xxx/
python douyin.py https://www.douyin.com/video/7652650092314316072
python douyin.py https://v.douyin.com/xxx/ --hd        # 高清版（如有）
python douyin.py https://v.douyin.com/xxx/ -o ./mydir   # 指定目录
```

### 仅查看信息

```bash
python douyin.py https://v.douyin.com/xxx/ --info
python douyin.py https://v.douyin.com/xxx/ --info --json
```

### 从分享文本提取

```bash
python douyin.py "7.43 FuL:/ 你别说 https://v.douyin.com/iFDbjn2M/ 复制此链接"
```

## 在 AI Agent 中使用

### Hermes Agent

```bash
# 技能会自动加载 SKILL.md
# 用户发抖音链接时，Agent 自动调用
hermes skill install https://github.com/xinyi-it/douyin-downloader
```

### Claude Code

把仓库克隆到技能目录：

```bash
git clone https://github.com/xinyi-it/douyin-downloader-skill.git ~/.claude/skills/douyin-downloader
```

### OpenClaw

```bash
# 1. 克隆到 OpenClaw skills 目录
git clone https://github.com/xinyi-it/douyin-downloader-skill.git ~/.openclaw/skills/douyin-downloader

# 2. 重启 gateway 生效
systemctl --user restart openclaw-gateway.service
```

OpenClaw 会自动加载 `SKILL.md`，用户发抖音链接时机器人会调用 `python douyin.py` 下载。

> ⚠️ 确保 OpenClaw 运行环境已安装 `requests`（`pip install requests`），且 `python3` 可用。

## 输出

| 项目 | 默认值 |
|------|--------|
| 保存目录 | `~/Documents/douyin_videos/` |
| 文件名 | `{video_id}.mp4` |
| 水印 | 无 ✅ |

## 工作原理

```
用户链接 → 解析短链接获取视频ID → 请求iesdouyin移动端页面 → 提取play_addr → /playwm/替换为/play/（去水印）→ 下载
```

不需要浏览器、不需要 Cookie、不需要 Selenium。纯 HTTP 请求搞定。

## 故障排查

| 问题 | 原因 | 解决 |
|------|------|------|
| "无法提取链接" | 分享文本不完整 | 让用户重新复制完整分享文本 |
| 短链接跳转到首页 | 链接已过期 | 让用户重新分享 |
| 下载 403 | 视频被删除或地区限制 | 换个视频试试 |
| 视频有水印 | playwm未被替换 | 提issue反馈 |

## 致谢

灵感来自 [xiaoyiv/douyin-skill](https://github.com/xiaoyiv/douyin-skill)，原版用 CDP 浏览器自动化，本版改为纯 HTTP 方案，更轻量更通用。

## 更新日志

### v1.0.0 (2026-06-24)

- 首个公开版本
- 纯 Python + requests，零浏览器依赖
- 支持短链接、完整URL、分享文本
- 无水印下载（/playwm/ → /play/）
- 适配 Hermes / Claude Code / OpenClaw

## License

MIT
