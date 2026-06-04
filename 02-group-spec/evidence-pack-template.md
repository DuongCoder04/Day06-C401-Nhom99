# Evidence Pack — Trợ Lý AI Tài Chính Chat-Based

Nộp kèm thin SPEC cuối Day 05.

## 1. Nhóm và track

**Tên nhóm:** Nguyễn Văn Dưỡng · Phùng Hữu Uy · Nguyễn Nhật Quang  
**Track:** Tài chính cá nhân  
**Product/app đã chọn:** MoMo — Moni  
**Build slice đang nghĩ:** Trợ lý AI tài chính chat-based — user nhắn tin tự nhiên để ghi chép, phân loại và thống kê chi tiêu

## 2. Self-use evidence

Nhóm tự dùng Moni trong app MoMo và ghi lại điểm gãy.

| Observation | Screenshot/link | Path liên quan | Điều học được |
|---|---|---|---|
| Moni nằm sâu trong hệ sinh thái MoMo — dù dùng MoMo thường xuyên vẫn không biết Moni tồn tại | — | Failure | Discovery problem: không có entry point rõ ràng, user không biết tính năng này để dùng |
| Moni rất lag khi mở bên trong app MoMo | — | Failure | Embedded trong app lớn → trải nghiệm chậm → user bỏ cuộc trước khi dùng thử |
| Tính năng quá ít so với kích thước app MoMo, không đủ giá trị để chịu lag | — | Promise | Value proposition không rõ — Moni không giải quyết một pain cụ thể đủ mạnh |
| Sau ~10 câu hỏi Moni "chạm trần" — hầu hết câu hỏi tài chính thực tế bị từ chối | — | Failure | Intent coverage hẹp: chỉ xử lý được lịch sử giao dịch, không hỗ trợ quản lý chi tiêu chủ động |
| Moni từ chối sớm, không hỏi lại hoặc chuyển hướng — user không có bước tiếp theo | — | Low-confidence | Fallback yếu: không có low-confidence path, không có handoff rõ ràng |
| Khi gửi prompt dài, màn hình bị freeze — các nút ngoài ô chat không tương tác được | — | Failure | Lỗi UI critical: mất khả năng điều hướng, gây cảm giác app treo |

## 3. User / review / social evidence

| Quote / review / observation | Nguồn | User là ai? | Pain/failure mode |
|---|---|---|---|
| "Không biết tại sao phải dùng Moni khi MoMo đã có sẵn lịch sử giao dịch" | Self-use observation | Người dùng MoMo hằng ngày | Value unclear — Moni không tạo ra giá trị rõ hơn tính năng có sẵn của MoMo |
| "Cuối tháng không biết tiền đi đâu, phải mở app ngân hàng xem lại từng giao dịch" | Self-use observation | Người đi làm quản lý tài chính cá nhân | Không có công cụ ghi chép chi tiêu nhanh và chủ động trong workflow hằng ngày |

```text
Đây là giả định từ self-use. Nhóm sẽ kiểm bằng phỏng vấn nhanh 2-3 người dùng MoMo thực tế
trước checkpoint M1 Day 06.
```

## 4. Competitor / analog evidence

| App / mô hình tham khảo | Họ xử lý task này thế nào? | Pattern học được | Có áp dụng trong 1 ngày không? |
|---|---|---|---|
| Money Lover | App standalone, user nhập thủ công từng giao dịch, chọn category | Standalone > embedded; category cố định giúp user dễ phân loại | ✅ Category structure có thể dùng ngay |
| Notion AI / ChatGPT | Chat tự nhiên → AI extract thông tin → ghi vào structured data | Chat-first interface giảm friction so với form nhập liệu | ✅ Core pattern của build slice |
| Splitwise | Ghi chi tiêu nhanh, phân loại, thống kê đơn giản | Simplicity wins — không cần nhiều tính năng, cần 1 flow thật nhanh | ✅ Scope discipline |

## 5. Evidence → Insight

```text
Evidence nổi bật nhất:
- Moni tồn tại nhưng không ai biết → discovery problem
- Moni lag và ít tính năng → friction > value
- User vẫn cần quản lý chi tiêu nhưng không có tool nhanh và tự nhiên để làm

Insight:
User không chỉ cần "một AI chatbot trong app tài chính".
Thật ra họ cần một cách ghi chép chi tiêu không có friction —
nhanh như nhắn tin, không cần mở app riêng, không cần nhớ format.
Vì evidence cho thấy: mọi friction (phải tìm Moni, chờ lag, nhập form) đều khiến user bỏ cuộc
trước khi tạo ra habit ghi chép.

Opportunity:
AI có thể giúp bằng cách nhận câu chat tự nhiên → tự extract số tiền, category, thời gian →
ghi vào log tự động,
giúp user có log chi tiêu chính xác mà không cần thay đổi hành vi.
```

## 6. Evidence đổi SPEC như thế nào?

- [x] Đổi build slice.
- [x] Đổi Auto/Aug decision.
- [x] Đổi 4 paths.
- [x] Đổi failure mode.

```text
Trước evidence, nhóm định build: CSV-based classifier — user upload file giao dịch,
AI gán nhãn tự động.

Sau evidence, nhóm đổi thành: Chat-based expense tracker — user nhắn tin tự nhiên,
AI extract và phân loại realtime.

Lý do:
Evidence chỉ ra rằng friction chính không phải ở việc "phân loại sai" mà ở việc
"user không bao giờ bắt đầu ghi chép vì tool quá phức tạp để vào".
CSV upload vẫn có friction cao. Chat = zero friction vì người dùng đã nhắn tin hằng ngày.
```
