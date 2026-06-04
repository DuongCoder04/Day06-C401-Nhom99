# Toolkit — Từ Evidence Đến Build Slice

Dùng sau khi nhóm đã có evidence. Mục tiêu là chốt một build slice đủ nhỏ cho Day 06.

## 1. Gom evidence thành cụm

Gom theo **workflow/pain**, không gom theo tên feature.

**Cụm 1: "Không biết tiền đi đâu cuối tháng"**
- User dùng MoMo hằng ngày nhưng không có thói quen ghi chép chi tiêu
- Cuối tháng phải mở lại lịch sử giao dịch, xem từng dòng, tự tổng hợp thủ công
- Không có công cụ nào đủ nhanh để ghi trong lúc chi tiêu

**Cụm 2: "Mọi tool ghi chi tiêu đều có friction quá cao"**
- Moni: phải tìm trong app MoMo → lag → ít tính năng → bỏ cuộc
- App chuyên dụng (Money Lover): phải mở app riêng → nhập form → chọn category → lưu
- Kết quả: không ai duy trì được habit ghi chép

**Cụm 3: "AI từ chối thay vì hỗ trợ"**
- Moni từ chối câu hỏi ngoài lịch sử giao dịch, không hỏi lại, không fallback
- User không có bước tiếp theo → mất tin tưởng vào AI tài chính

## 2. Viết insight

```text
User đi làm quản lý tài chính cá nhân không chỉ cần "một app phân loại chi tiêu".
Họ thật ra cần một cách ghi chép không có friction — nhanh như nhắn tin,
không cần mở thêm app, không cần nhớ bất kỳ format nào,
vì evidence cho thấy mọi friction nhỏ (lag, phải tìm, phải nhập form) đều đủ để
phá vỡ habit ghi chép.
```

## 3. Viết opportunity

```text
Cơ hội là dùng AI để nhận câu chat tự nhiên về chi tiêu,
tự extract số tiền + category + thời gian và ghi vào log tự động,
giúp user có log chi tiêu chính xác mà không thay đổi hành vi hằng ngày,
trong khi vẫn kiểm soát được trường hợp câu thiếu thông tin (hỏi lại hoặc gán Khác).
```

## 4. Chọn build slice

| Câu hỏi | Đánh giá |
|---|---|
| User cụ thể chưa? | ✅ Người đi làm dùng MoMo hằng ngày, muốn biết tiền đi đâu cuối tháng |
| Task đủ hẹp chưa? | ✅ Nhắn 1 câu → AI ghi vào log → hỏi thống kê → AI trả lời. Demo được trong 3 phút |
| AI decision rõ chưa? | ✅ AI extract: số tiền + category + ngày từ câu text tự nhiên |
| Failure path rõ chưa? | ✅ Câu thiếu số tiền hoặc category mơ hồ → AI hỏi lại hoặc gán "Khác" |
| Có evidence không? | ✅ Self-use Moni + competitor analysis + pain observation |

→ **Build slice đạt đủ 5 tiêu chí. Giữ nguyên.**

## 5. Quyết định: giữ, giảm scope, hay đổi hướng?

| Tình huống | Đánh giá |
|---|---|
| Evidence yếu, user mơ hồ | ❌ Evidence có từ self-use, rõ |
| Ý tưởng quá rộng | ⚠️ Scope đã cắt: chỉ text, không có chart/ảnh, không auth |
| AI không cần thiết | ❌ AI cần thiết để extract từ câu tự nhiên — rule-based không đủ |
| Rủi ro cao | ✅ Augmentation — user có thể sửa nếu AI gán sai |
| Không demo được trong 1 ngày | ✅ Demo được: chat → ghi → hỏi thống kê |

**Quyết định: Giữ scope hiện tại.**

## 6. Câu chốt cuối

```text
Dựa trên self-use evidence (Moni lag + discovery problem + intent coverage hẹp)
và competitor analysis (chat-first < form-based về friction),
nhóm sẽ build chat-based AI expense tracker,
cho người dùng MoMo đang không có thói quen ghi chép chi tiêu vì tool quá phức tạp,
để giải quyết pain: không biết tiền đi đâu cuối tháng,
bằng cách AI tự extract số tiền + category + ngày từ câu chat tự nhiên và ghi vào log,
và sẽ test failure path: câu thiếu số tiền hoặc mô tả quá mơ hồ.
```

## 7. Backlog

Những thứ **không build trong Day 06**:

- Nhận diện ảnh hoá đơn / bill
- Dashboard chart / visualization
- User-defined category
- Authentication / multi-user
- Export CSV / báo cáo định kỳ
- Tích hợp trực tiếp với MoMo API
