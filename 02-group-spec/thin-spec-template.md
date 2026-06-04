# Thin SPEC — Trợ Lý AI Tài Chính Chat-Based

Thin SPEC không phải PRD đầy đủ. Đây là bản cam kết đủ rõ để sáng Day 06 nhóm build ngay.

## 1. Track, product/app và user

**Track:** Tài chính cá nhân  
**Product/app thật:** MoMo — Moni (app được mổ xẻ; prototype là giải pháp thay thế standalone)  
**User cụ thể:** Người đi làm (22–35 tuổi) dùng MoMo hằng ngày, muốn quản lý chi tiêu cá nhân nhưng không duy trì được thói quen ghi chép vì mọi tool hiện tại đều có friction cao  
**Nhóm có phải user thật không?** Có — thành viên nhóm dùng MoMo và đã self-use Moni. Điểm khác: nhóm có technical background, user thật có thể ít kiên nhẫn hơn với lỗi.

## 2. Evidence summary

| Evidence | Nguồn | User/pain nói lên điều gì? | SPEC phải đổi gì? |
|---|---|---|---|
| Moni lag, khó tìm trong MoMo, người dùng không biết nó tồn tại | Self-use Moni | Friction > value → user bỏ cuộc trước khi dùng | Build standalone, không embedded |
| Sau ~10 câu hỏi Moni từ chối hầu hết, không hỏi lại | Self-use Moni | AI không có low-confidence path → mất tin tưởng | Phải có path hỏi lại khi thiếu thông tin |
| Cuối tháng không biết tiền đi đâu, phải xem lại lịch sử thủ công | Self-use observation | Pain thật: thiếu tool ghi chép nhanh trong workflow hằng ngày | Chat-first interface, không phải CSV upload |
| Money Lover dùng category cố định, Splitwise ưu tiên simplicity | Competitor analysis | Category cố định + single flow wins | Dùng 6 category cố định, không user-defined |

## 3. Pain statement

```text
Người dùng MoMo (22–35 tuổi, đi làm) đang gặp khó ở bước ghi chép và theo dõi chi tiêu hằng ngày,
vì mọi tool hiện có đều có friction cao (phải mở app riêng, nhập form, chờ lag),
dẫn tới việc không duy trì được thói quen ghi chép và cuối tháng không biết tiền đi đâu.
Bằng chứng chính là: self-use Moni cho thấy lag + khó tìm + ít tính năng = không có lý do để dùng;
observation cá nhân: phải xem lại lịch sử giao dịch ngân hàng thủ công để tổng kết chi tiêu.
```

## 4. Build slice

```text
Cho người dùng MoMo đang muốn ghi lại chi tiêu vừa phát sinh (ví dụ: vừa ăn sáng, vừa đổ xăng),
prototype sẽ dùng AI để nhận câu chat tự nhiên, extract số tiền + category + ngày giờ,
và tự động ghi vào log chi tiêu theo 6 nhóm cố định (Ăn uống / Di chuyển / Mua sắm / Giải trí / Hóa đơn / Khác),
tạo ra log chi tiêu realtime và trả lời thống kê qua text khi user hỏi,
và xử lý câu thiếu thông tin (không có số tiền hoặc mô tả mơ hồ) bằng cách
hỏi lại user — nếu user vẫn không cung cấp thêm thì gán vào "Khác" với số tiền user đã nhớ.
```

## 5. Auto/Aug decision

- [x] **Conditional automation:** AI tự làm trong case hẹp (câu rõ ràng có đủ số tiền + mô tả); case mơ hồ/thiếu thông tin → hỏi lại user.

**Lý do chọn:** Ghi chép chi tiêu cần tốc độ cao (tự động hóa khi đủ thông tin) nhưng accuracy quan trọng hơn convenience khi thiếu thông tin — sai category = data không tin được.  
**Human role:** Decider — user quyết định khi AI không chắc; user có thể sửa category sau khi đã ghi.

## 6. Four paths

| Path | Prototype phải thể hiện gì? |
|---|---|
| Happy | User nhắn "Sáng nay ăn phở 35k" → AI extract đúng: 35,000đ / Ăn uống / hôm nay sáng → confirm ghi vào log → user nhắn "Hôm nay tôi tiêu bao nhiêu?" → AI trả lời chính xác |
| Low-confidence | User nhắn "Hôm qua tôi tiêu nhiều lắm" (không có số tiền) → AI hỏi lại: "Bạn tiêu bao nhiêu và cho việc gì?" → user trả lời → AI ghi đúng |
| Failure | User nhắn một câu hoàn toàn không liên quan đến chi tiêu → AI nhận ra không phải giao dịch, không ghi vào log, giải thích ngắn gọn |
| Correction | User thấy AI gán sai category → nhắn "Sửa lại cái vừa ghi thành Di chuyển" → AI cập nhật đúng trong log |

## 7. Failure mode nguy hiểm nhất

```text
Nếu user nhắn câu mơ hồ không có số tiền cụ thể (ví dụ: "Hôm nay tôi tiêu hết tiền rồi"),
AI có thể tự bịa số tiền hoặc ghi nhầm entry không có thật vào log,
hậu quả là log chi tiêu sai → thống kê sai → user mất tin tưởng vào toàn bộ tool.
Prototype sẽ xử lý bằng: hỏi lại bắt buộc khi không có số tiền rõ ràng;
nếu sau 1 lần hỏi lại user vẫn không cung cấp số, ghi "Khác — chưa rõ số tiền" để không mất thông tin nhưng không bịa số.
Owner kiểm thử path này là: Nguyễn Văn Dưỡng.
```

## 8. Owner plan cho sáng Day 06

| Thành viên | Việc phụ trách | Bằng chứng cần có trong repo |
|---|---|---|
| Nguyễn Văn Dưỡng | Prototype (chat interface + AI extraction logic) | Code chạy được, README hướng dẫn chạy |
| Phùng Hữu Uy | Research / evidence bổ sung + SPEC hoàn thiện | evidence-pack-template.md đã điền đủ |
| Nguyễn Nhật Quang | Test failure path + demo script | Test cases ghi rõ input/output thực tế, script demo 3 phút |
