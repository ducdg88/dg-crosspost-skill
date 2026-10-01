# dg-crosspost-skill

[Tiếng Việt](#tiếng-việt) | [English](#english)

## Tiếng Việt

Skill cho Claude Code: bài đã đăng lên Page được tự xếp lịch đẩy sang Zalo, nhóm Zalo, TikTok, YouTube. Có luật giờ: gửi trong khung 07:00 đến 22:00 giờ Việt Nam, quá 22:00 thì hẹn lại sáng mai 07:30, các nền tảng cách nhau vài phút để không bị coi là spam.

- Mặc định chạy khô, không gửi gì. `--thuc-su` mới gửi thật.
- Chỉ ghi "đã đăng" khi nền tảng trả về link bài.
- Không có khóa nào trong repo. Khóa và địa chỉ webhook nằm trong biến môi trường của máy.
- Không cần thư viện ngoài, chỉ cần Python 3.9 trở lên.

Dùng nhanh:

```bash
cp config.example.json config.json            # config.json đã nằm trong .gitignore
python scripts/kiem_ket_noi.py --tu-kiem      # tự kiểm, không gửi gì
python scripts/kiem_ket_noi.py --config config.json --ping
python scripts/crosspost.py --config config.json enqueue-file post.json
python scripts/crosspost.py --config config.json run            # chạy khô
python scripts/crosspost.py --config config.json run --thuc-su  # gửi thật
python -m unittest discover -s tests
```

Chi tiết và giới hạn từng nền tảng: xem `SKILL.md`. Cài vào Claude Code: chép thư mục này vào `~/.claude/skills/dg-crosspost-nhieu-nen-tang/`.

## English

A Claude Code skill: a post already published on a Facebook Page is queued for Zalo, Zalo groups, TikTok and YouTube. Posting-hours rule: send between 07:00 and 22:00 Vietnam time (UTC+7); after 22:00 it is deferred to 07:30 the next morning; platforms are staggered by a few minutes to avoid looking like spam.

- Dry-run by default, nothing is sent. `--thuc-su` sends for real.
- "Posted" is recorded only when the platform returns a post link.
- No secrets in the repo. Keys and webhook URLs live in environment variables.
- No third-party dependencies, Python 3.9+.

Quick start: see the commands above. Details and per-platform limits are in `SKILL.md`. Install: copy this folder to `~/.claude/skills/dg-crosspost-nhieu-nen-tang/`.

## License

MIT
