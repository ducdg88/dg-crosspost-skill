---
name: dg-crosspost-nhieu-nen-tang
description: Tự đẩy bài đã đăng lên Page sang các nền tảng khác (Zalo, nhóm Zalo, TikTok, YouTube...) kèm luật giờ đăng, gửi được trong khung 07:00 đến 22:00, quá 22:00 thì hẹn lại sáng mai 07:30, các nền tảng cách nhau vài phút để không bị coi là spam. Dùng khi nói "đăng bài lên Page thì tự đẩy sang Zalo, TikTok, YouTube", "đẩy bài đa nền tảng", "crosspost", "đăng chéo", "hẹn giờ đăng sáng mai", "qua 10h tối thì hẹn lại", "đẩy sang nhóm Zalo". Không dùng để tạo nội dung hay video (dg-content-social, dg-maps-video-thuong-hieu) và không dùng để đăng lên chính Page (fanpage autopilot).
---

# /dg-crosspost-nhieu-nen-tang

Bài đã lên Page và có link công khai kiểm chứng được thì được xếp lịch đẩy sang các nền tảng khác. Mặc định chạy khô, không gửi gì ra ngoài, muốn gửi thật phải thêm `--thuc-su`. English summary at the end.

## Luật giờ (đã chọn, muốn khác thì sửa `config.json`)

- Gửi được từ 07:00 đến 22:00 giờ Việt Nam (UTC+7). Gửi được tới hết 22:00.
- Qua 22:00 thì hẹn sáng mai 07:30. Trước 07:00 thì hẹn 07:30 cùng ngày.
- Các nền tảng cách nhau `gian_cach_phut` (mặc định 10). Nền tảng nào rớt ra ngoài khung thì sang sáng mai, xếp tiếp 07:30, 07:40...
- Giờ được kiểm lại lúc gửi thật, không tin giờ đã xếp từ trước.
- Hiểu từ lời Founder: "trong giờ hành chính hoặc ngoài giờ nhưng chỉ tới 10h tối". Mình chọn một khung 07:00 đến 22:00 cho mọi ngày. Muốn tách giờ hành chính riêng thì đổi `gio_bat_dau`.

## Dùng khi nào

- Bài vừa lên Page và Founder muốn có mặt ở Zalo, TikTok, YouTube, nhóm Zalo.
- Cần xem hàng đợi, bài nào đang chờ giờ, bài nào hẹn sang mai.

## Không dùng khi

- Cần viết bài hay làm video: `dg-content-social`, `dg-maps-video-thuong-hieu`.
- Đăng lên chính Page: Fanpage Autopilot. Skill này chỉ đẩy sang nơi khác.

## Cách chạy

Cài: chép thư mục này vào `~/.claude/skills/dg-crosspost-nhieu-nen-tang/`. Chép `config.example.json` thành `config.json` (file này bị `.gitignore`, không được đưa lên GitHub).

1. Kiểm kết nối, không gửi: `python scripts/kiem_ket_noi.py --config config.json --ping`. Chỉ in tên biến môi trường có hay thiếu, không in giá trị.
2. Tự kiểm tròn mạch ở thư mục tạm: `python scripts/kiem_ket_noi.py --tu-kiem` (chạy 4 kiểm tra: `.gitignore`, quét rò rỉ, xếp lịch, chạy khô).
3. Xếp lịch từ bài đã lên Page: `python scripts/crosspost.py --config config.json enqueue-state <state.json của Fanpage Autopilot> [--page ID]`. Chỉ lấy bài `public` có proof HTTP 200 và có link. Hoặc từng bài: `enqueue-file post.json` với `text`, `permalink`, `media`.
4. Chạy khô xem sẽ gửi gì: `python scripts/crosspost.py --config config.json run`.
5. Gửi thật, sau khi Founder đồng ý: thêm `--thuc-su`. Muốn tự động thì đặt tác vụ nền mỗi 5 phút chạy lệnh ở bước 3 rồi `run --thuc-su`, chạy ẩn.
6. Xem hàng đợi: `python scripts/crosspost.py --config config.json status`.

## Cách nối từng nền tảng

Mỗi nền tảng khai `kieu` trong `config.json`:
- `webhook`: gửi JSON tới địa chỉ nằm trong biến môi trường (https hoặc loopback). Công cụ đăng của bạn trả về `permalink` thì mới ghi "đã đăng".
- `outbox`: ghi file JSON vào thư mục để công cụ khác (ví dụ trình duyệt tự động) tự lấy. Cách này hợp với nhóm Zalo.

Giới hạn cần biết (kiến thức đến giữa 2026, kiểm lại tài liệu chính thức trước khi dựa vào):
- YouTube Data API: mỗi lần tải tốn khoảng 1.600 đơn vị trong hạn mức 10.000 mỗi ngày, tức tối đa khoảng 6 video mỗi ngày. Dự án API chưa được xác minh thì video có thể bị ép riêng tư.
- TikTok Content Posting API: ứng dụng chưa qua kiểm duyệt chỉ đăng được ở chế độ riêng tư.
- Zalo: không có API chính thức để đăng vào nhóm cá nhân. API của Official Account gửi tin tới người theo dõi, có quy định riêng. Tự động hóa tài khoản cá nhân có rủi ro bị khóa: cân nhắc trước khi bật.

## Bí mật và rò rỉ

- Khóa, token, địa chỉ webhook chỉ nằm trong biến môi trường của máy. Không ghi vào `config.json`, log hay hàng đợi. Lỗi in ra đã được che chuỗi giống khóa.
- Hàng đợi `queue/`, thư mục `outbox/`, `config.json` đều nằm trong `.gitignore`.
- Chỉ gửi nội dung đã công khai (chữ, link bài gốc, tên file media). Không gửi dữ liệu khách, số tiền, đường dẫn máy.
- Trước khi đẩy lên GitHub luôn chạy `--tu-kiem`.

## Không làm

- Không gửi thật khi chưa có `--thuc-su` và chưa được Founder đồng ý lần đầu.
- Không báo "đã đăng" khi nền tảng chưa trả link bài. Trạng thái đó là `cho_proof`.
- Không đăng dồn: một bài chỉ xếp một lần cho mỗi nền tảng (chống trùng theo mã bài), các nền tảng cách nhau.
- Không nới khung giờ hay gian cách để đẩy nhanh hàng tồn.
- Không dùng dấu gạch dài trong nội dung: `bo_gach_dai` mặc định bật và tự đổi thành dấu phẩy.

## Xong khi

Mỗi bài đủ trạng thái cuối trên mọi nền tảng bật: `da_dang` kèm link, hoặc `hen_lai` có giờ sáng mai, hoặc `loi` kèm lý do đã che khóa. Không bài nào nằm im ở `cho` quá giờ.

## Eval

| Chỉ số | Cách đo | Đích |
|---|---|---|
| Luật giờ | `python -m unittest discover -s tests` | 6/6 |
| Không rò rỉ | `kiem_ket_noi.py --tu-kiem` | KẾT QUẢ: ĐẠT |
| Không báo đăng giả | số bài `da_dang` thiếu `proof` | 0 |

## Sổ feedback

| Ngày | Chuyện gì xảy ra | Đã sửa gì |
|---|---|---|
| 01/10/2026 | Tạo skill, 6 test giờ, tự kiểm đạt, thử gửi vào outbox tạm: chống trùng đúng, không báo đăng giả | v1 |

## English summary

Queues a Page post (public, proof HTTP 200) for other platforms. Send window 07:00 to 22:00 (UTC+7); after 22:00 it is deferred to 07:30 next day; platforms are staggered. Dry-run by default, `--thuc-su` sends for real. A post is `da_dang` only when the platform returns a permalink. No secrets in files or logs; run `kiem_ket_noi.py --tu-kiem` before every push.
