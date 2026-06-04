# Workshop — Mổ App AI Thật

**Thời gian:** 35-45 phút  
**Hình thức:** cá nhân trước, chia sẻ theo nhóm sau  
**Output:** finding note + sketch `as-is / to-be`

Mục tiêu không phải chấm "UI đẹp hay xấu". Mục tiêu là dùng sản phẩm thật như một bài needfinding: tìm chỗ product gãy trong workflow thật, rồi viết finding đó thành quyết định product.

---

**Thành viên nhóm:**
- Nguyễn Văn Dưỡng — 2A202600967
- Phùng Hữu Uy — 2A202600886
- Nguyễn Nhật Quang — 2A202600813

**Sản phẩm chọn:** MoMo — Moni

---

## 1. Chọn một sản phẩm để dùng thử

| Sản phẩm | AI feature | Cách truy cập |
|---|---|---|
| MoMo — Moni | Trợ thủ tài chính, phân tích chi tiêu, chatbot | App MoMo |
| Vietnam Airlines — NEO | Chatbot hỗ trợ vé, hành lý, khiếu nại | Website/Zalo VNA |
| V-App — V-AI | Trợ lý voice/text, gợi ý theo ngữ cảnh | App V-App |

**Sản phẩm đã chọn:** MoMo — Moni

**Bối cảnh sản phẩm:** Moni được định vị là trợ lý tài chính cá nhân trong hệ sinh thái MoMo, thiên về theo dõi chi tiêu, phân tích giao dịch, lập ngân sách, nhắc hóa đơn và gợi ý tiết kiệm. MoMo có nhiều kênh hỗ trợ song song (Trung tâm trợ giúp, Chat với MoMo, trang hướng dẫn), cho thấy Moni chỉ là một phần trong hệ thống hỗ trợ rộng hơn.

**Mục tiêu test:** Đánh giá mức độ hữu ích thực tế của Moni qua 4 khía cạnh: khả năng hiểu intent, độ rộng phạm vi hỗ trợ, độ bền hội thoại khi hỏi liên tục, và chất lượng trải nghiệm khi gặp input dài hoặc trường hợp từ chối.

## 2. Dùng thử: promise vs reality

**Product hứa gì?**  
Moni tự mô tả có thể: theo dõi và phân loại chi tiêu, lập kế hoạch ngân sách, phân tích báo cáo theo ngày/tuần/tháng, đưa mẹo tiết kiệm, gợi ý tài chính cá nhân, nhắc hóa đơn, hỗ trợ mục tiêu tài chính, giải thích danh mục chi tiêu và thống kê giao dịch. MoMo truyền thông Moni như công cụ giúp người dùng "quán xuyến tiền bạc hiệu quả".

**User nào được hứa sẽ được giúp?**  
Người dùng MoMo hằng ngày cần quản lý tài chính cá nhân: theo dõi chi tiêu, phân tích giao dịch, lập ngân sách, xử lý các vấn đề liên quan đến thanh toán.

**Kỳ vọng AI làm được task nào?**  
Hỗ trợ đa dạng tình huống tài chính: lịch sử giao dịch, sao bị trừ tiền, hoàn tiền, giao dịch lỗi, nạp/rút/chuyển tiền, hóa đơn, ngân sách, gợi ý tiết kiệm.

**Điểm gãy xuất hiện ở đâu?**

| Observation | Path liên quan | Điều học được |
|---|---|---|
| Moni chỉ xử lý tốt câu hỏi về lịch sử giao dịch; các câu hỏi khác bị từ chối | Failure | Happy path bị co hẹp thành một nhánh đơn lẻ |
| Sau ~10 câu hỏi, Moni "chạm trần" — hầu hết câu hỏi tài chính phổ biến bị từ chối | Failure | Độ phủ intent thấp, độ bền hội thoại yếu |
| Gửi prompt rất dài → màn hình đơ hoàn toàn, các nút ngoài ô chat không tương tác được | Failure | Lỗi UI freeze mức critical, mất khả năng điều hướng |
| Moni từ chối sớm các câu hỏi về hoàn tiền, giao dịch lỗi, khiếu nại mà không hỏi lại hay chuyển hướng | Low-confidence | Fallback yếu, người dùng không có bước tiếp theo |
| Khi hỏi "làm được gì", Moni liệt kê phạm vi rộng nhưng thực tế xử lý hẹp hơn nhiều | Promise | Gap giữa marketing intent và thực tế sử dụng |

**Evidence có:**
- Prompt/input đã thử: ~10 câu hỏi tài chính thường gặp, 1 prompt rất dài
- Hành vi quan sát được: từ chối sớm, UI freeze khi prompt dài, chỉ hoạt động tốt ở nhánh lịch sử giao dịch

## 3. Vẽ 4 paths

| Path | Câu hỏi cần trả lời | Quan sát thực tế |
|---|---|---|
| Happy | Khi AI đúng và tự tin, user thấy gì? | Moni hoạt động tốt nhất với câu hỏi về lịch sử giao dịch và tra cứu giao dịch cụ thể. User nhận được thông tin đúng, dẫn vào đúng ngữ cảnh. |
| Low-confidence | Khi AI không chắc, hệ thống có hỏi lại, show options hoặc chuyển người không? | **Không có.** Moni từ chối thẳng thay vì hỏi lại hoặc chuyển hướng sang kênh phù hợp. User không có bước tiếp theo rõ ràng. |
| Failure | Khi AI sai, user biết bằng cách nào và sửa thế nào? | Moni từ chối hoặc không xử lý được. User không biết phải làm gì tiếp theo. Nghiêm trọng hơn: khi gửi prompt dài, màn hình freeze — user không thể thoát hoặc điều hướng. |
| Correction | Khi user sửa, correction có được lưu/log/học lại không hay biến mất? | **Không quan sát được path này** — Moni không đủ đất để sai rồi được sửa trong hầu hết các case, vì đã từ chối trước khi tạo ra output cần correction. |

## 4. Viết finding thành quyết định

**Finding 1 — Intent coverage hẹp:**

```text
Khi user hỏi các câu hỏi tài chính phổ biến ngoài lịch sử giao dịch
(sao bị trừ tiền, giao dịch lỗi, hoàn tiền, chuyển tiền chưa nhận, hóa đơn, khiếu nại),
AI từ chối mà không hỏi lại hoặc chuyển hướng,
hậu quả là user không có bước tiếp theo và mất niềm tin vào trợ lý.
Lỗi thuộc layer Promise + Intent.
Nên sửa bằng: mở rộng intent cho nhóm tình huống tài chính phổ biến;
khi ngoài phạm vi, dùng fallback rõ ràng → chuyển sang Trung tâm trợ giúp hoặc Chat với MoMo.
```

**Finding 2 — Độ bền hội thoại yếu:**

```text
Khi user hỏi liên tục ~10 câu trong một phiên,
Moni chạm ngưỡng sử dụng sớm và hầu hết câu hỏi bị từ chối,
hậu quả là user cảm giác "hết lượt" và không có lý do tiếp tục dùng Moni.
Lỗi thuộc layer Intent + UX Recovery.
Nên sửa bằng: tăng độ phủ intent, duy trì context qua nhiều lượt hỏi,
và thiết kế handoff rõ ràng thay vì từ chối đơn thuần.
```

**Finding 3 — UI freeze với prompt dài (P0):**

```text
Khi user gửi prompt rất dài,
màn hình Moni bị đơ hoàn toàn — các nút ngoài ô chat không tương tác được,
hậu quả là user mất khả năng điều hướng, cảm giác app treo, phải tắt/mở lại.
Lỗi thuộc layer UX Recovery (critical).
Nên sửa bằng: giới hạn và xử lý an toàn input dài;
thêm loading state rõ ràng và đảm bảo nút hủy/back/home luôn khả dụng.
```

## 5. Sketch as-is / to-be

**As-is — Flow hiện tại:**

```
User mở Moni
    │
    ▼
Hỏi về lịch sử giao dịch
    │
    ▼
[HAPPY PATH] Moni trả lời đúng ✓
    │
    ├── Hỏi câu hỏi tài chính khác (hoàn tiền, giao dịch lỗi, hóa đơn...)
    │       │
    │       ▼
    │   [FAILURE ✗] Moni từ chối sớm
    │       │
    │       ▼
    │   User không có bước tiếp theo → thoát khỏi Moni
    │
    └── Gửi prompt rất dài
            │
            ▼
        [FAILURE ✗] UI FREEZE — màn hình đơ
            │
            ▼
        User mất khả năng điều hướng → buộc tắt/mở lại app
```

**Điểm gãy:** Từ chối sớm không kèm fallback + UI freeze với prompt dài.

---

**To-be — Flow đề xuất:**

```
User mở Moni
    │
    ▼
Hỏi bất kỳ câu hỏi tài chính phổ biến
    │
    ├── Intent rõ + trong phạm vi
    │       │
    │       ▼
    │   [HAPPY PATH] Moni xử lý và trả lời ✓
    │
    ├── Intent mơ hồ / không đủ thông tin
    │       │
    │       ▼
    │   [LOW-CONFIDENCE] Moni hỏi lại ngắn gọn
    │       │
    │       ▼
    │   User làm rõ → Moni xử lý tiếp ✓
    │
    ├── Intent ngoài phạm vi Moni
    │       │
    │       ▼
    │   [FALLBACK] Moni thừa nhận giới hạn
    │       + Gợi ý bước tiếp theo rõ ràng:
    │         → "Bạn có thể vào Trung tâm trợ giúp / Chat với MoMo"
    │
    └── Gửi prompt dài
            │
            ▼
        [SAFE HANDLING] Hiển thị loading state
        Nút back/home luôn khả dụng
        Giới hạn input hoặc xử lý async không block UI ✓
```

**Path đã sửa:** Low-confidence path có hỏi lại; Failure path có fallback rõ ràng; UI luôn responsive.

## 6. Tự kiểm trước khi nộp

- [x] Có ít nhất 1 screenshot hoặc observation cụ thể — *đã ghi observation từ ~10 câu hỏi test và lỗi UI freeze.*
- [x] Có đủ 4 paths hoặc nói rõ path nào chưa có — *đã mô tả đủ 4 paths; Correction path không quan sát được vì Moni từ chối trước khi tạo output.*
- [x] Finding được viết thành product decision, không chỉ là nhận xét — *3 finding đã theo đúng format: trigger → failure → impact → layer → cách sửa.*
- [x] Sketch có as-is và to-be — *đã vẽ text-based flow với điểm gãy và path đã sửa.*
- [x] Có một câu nói rõ finding này sẽ đổi gì trong SPEC:

> **Finding này đổi SPEC ở chỗ:** Build slice không thể chỉ nhắm vào lịch sử giao dịch (happy path hiện tại của Moni) mà cần giải quyết đúng điểm gãy — cụ thể là thiết kế low-confidence path và fallback handoff cho các câu hỏi tài chính phổ biến bị từ chối. Đồng thời, failure mode nghiêm trọng nhất cần đưa vào SPEC là lỗi UI freeze với input dài.
