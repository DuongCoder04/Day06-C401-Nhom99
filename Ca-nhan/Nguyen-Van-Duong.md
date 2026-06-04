# Nguyễn Văn Dưỡng — 2A202600967

## Ý tưởng cá nhân: AI Quản Lý Tài Chính Cá Nhân

---

## 1. Vấn đề

Người trẻ Việt Nam — sinh viên, người đi làm mới — thường gặp 3 vấn đề cốt lõi khi quản lý tài chính:

**1. Không biết tiền đi đâu**
Mỗi tháng tiêu xong rồi mới nhận ra hết tiền, nhưng không rõ mình đã tiêu vào đâu. Việc ghi chép thủ công (spreadsheet, app) đòi hỏi kỷ luật cao — đa số bỏ cuộc sau vài tuần.

**2. Lập ngân sách nhưng không giữ được**
Biết nên tiết kiệm, nhưng không có cơ chế nhắc nhở hay cảnh báo khi sắp vượt ngân sách. Chỉ biết sau khi đã vượt.

**3. Không có người tư vấn tài chính cá nhân**
Cố vấn tài chính dành cho người có thu nhập cao. Người bình thường không có nơi để hỏi những câu đơn giản: "Tháng này tôi có nên mua iPhone không?", "Tôi đang tiêu nhiều vào đâu?", "Tiết kiệm bao lâu thì đủ tiền mua xe máy?"

---

## 2. Giải pháp đề xuất

**FinBuddy** — Trợ lý tài chính cá nhân AI, hoạt động qua hội thoại tự nhiên.

Thay vì người dùng phải tự nhập liệu và đọc biểu đồ, FinBuddy chủ động:
- **Hỏi** để hiểu tình huống tài chính hiện tại
- **Nhắc** khi người dùng sắp vượt ngân sách
- **Phân tích** các mẫu chi tiêu theo ngữ cảnh thực tế
- **Trả lời** các câu hỏi tài chính thường ngày bằng ngôn ngữ bình thường

> *"Tháng này mình đã tiêu bao nhiêu tiền ăn uống?"*
> *"Còn bao nhiêu tiền để tiêu đến cuối tháng?"*
> *"Mình có nên mua cái này không?"*

---

## 3. Học được gì từ bài teardown MoMo Moni

Khi test Moni — sản phẩm gần nhất với FinBuddy trên thị trường — nhóm phát hiện ra 3 lỗ hổng lớn:

| Lỗ hổng của Moni | Bài học cho FinBuddy |
|-----------------|---------------------|
| Happy path quá hẹp (chỉ query lịch sử giao dịch) | Cần phủ rộng các câu hỏi tài chính thường ngày, không chỉ tra cứu |
| Từ chối sớm, không hỏi lại, không chuyển hướng | Low-confidence path phải có: hỏi lại hoặc fallback rõ ràng |
| UI freeze với input dài — lỗi critical | Input validation + non-blocking UI từ đầu |
| Gap lớn giữa promise và thực tế | Chỉ hứa đúng những gì làm được trong MVP |

**Điểm khác biệt FinBuddy muốn giải quyết:**
Moni chủ yếu là *query tool* (tra cứu lịch sử). FinBuddy muốn là *advisory layer* (tư vấn theo ngữ cảnh) — không chỉ trả lời "bạn đã tiêu gì" mà còn "bạn nên làm gì tiếp theo".

---

## 4. Core User Experience

### Flow tổng quan

```
User → FinBuddy → Hiểu câu hỏi tài chính
               → Truy xuất dữ liệu chi tiêu (từ lịch sử / input thủ công)
               → Phân tích theo ngữ cảnh
               → Trả lời + Gợi ý hành động
```

### Các tình huống điển hình

**1. Báo cáo chi tiêu nhanh**
> "Tháng này mình tiêu bao nhiêu tiền ăn uống?"
FinBuddy tổng hợp từ lịch sử, đưa con số cụ thể + so sánh với tháng trước.

**2. Cảnh báo ngân sách**
> Người dùng đặt ngân sách ăn uống 2 triệu/tháng.
> Khi đến 80% → FinBuddy tự động nhắc: "Bạn còn 400k cho ăn uống đến cuối tháng."

**3. Tư vấn quyết định chi tiêu**
> "Mình có nên mua iPhone 16 không?"
FinBuddy nhìn vào thu nhập, tiết kiệm hiện tại, các mục tiêu tài chính và đưa ra góc nhìn thực tế.

**4. Lập kế hoạch mục tiêu**
> "Mình muốn tiết kiệm 20 triệu để mua xe máy."
FinBuddy tính toán: cần tiết kiệm bao nhiêu/tháng, mất bao lâu với thói quen hiện tại.

---

## 5. AI Layer — Thiết kế cốt lõi

### Intents cần hỗ trợ

| Intent | Ví dụ câu hỏi |
|--------|--------------|
| `SPENDING_QUERY` | "Tháng này tiêu bao nhiêu?", "Tiêu nhiều nhất vào đâu?" |
| `BUDGET_CHECK` | "Còn bao nhiêu ngân sách?", "Có vượt budget không?" |
| `DECISION_ADVICE` | "Có nên mua cái này không?", "Tiêu khoản này có hợp lý không?" |
| `SAVING_GOAL` | "Bao lâu thì tiết kiệm đủ X tiền?" |
| `CATEGORY_ANALYSIS` | "So sánh chi tiêu tháng này với tháng trước" |
| `ADD_TRANSACTION` | "Hôm nay mình tiêu 150k ăn trưa" |
| `SET_BUDGET` | "Đặt ngân sách ăn uống 2 triệu/tháng" |

### System Prompt concept

```
Bạn là FinBuddy, trợ lý tài chính cá nhân thông minh.
Bạn nói tiếng Việt, thân thiện nhưng thực tế — không hoa mỹ.
Bạn hiểu người dùng không phải chuyên gia tài chính → giải thích đơn giản.

Dữ liệu tài chính của user:
- Thu nhập/tháng: {monthly_income}
- Ngân sách theo danh mục: {budget_categories}
- Chi tiêu tháng này: {current_month_spending}
- Tiết kiệm hiện tại: {savings}
- Mục tiêu đang theo dõi: {financial_goals}

Rules:
1. Luôn dùng số liệu thực tế từ dữ liệu user, không đoán mò.
2. Khi không có dữ liệu → hỏi user cung cấp.
3. Lời khuyên phải cụ thể, có con số thực tế.
4. Không phán xét thói quen tiêu dùng của user.
```

---

## 6. Điểm khác biệt so với Moni / các app hiện tại

| Tính năng | Moni (MoMo) | App thông thường (Money Lover...) | FinBuddy |
|-----------|-------------|----------------------------------|---------|
| Nhập giao dịch | Tự động (từ MoMo) | Thủ công | Hỗ trợ cả 2 |
| Trả lời câu hỏi tự nhiên | Hẹp (chủ yếu query) | ❌ | Rộng (advisory) |
| Tư vấn quyết định | ❌ | ❌ | ✅ |
| Cảnh báo ngân sách | Hạn chế | Có | Có + proactive |
| Hội thoại đa lượt | Yếu | ❌ | ✅ |
| Fallback path | Kém | N/A | Rõ ràng |

---

## 7. MVP Scope (nếu build 1 ngày)

Tập trung vào core AI value — đủ để demo được điểm khác biệt so với Moni:

1. **Chat interface** — hỏi đáp tài chính tự nhiên
2. **Mock financial data** — thu nhập, chi tiêu theo danh mục, ngân sách
3. **3 intents chính:** `SPENDING_QUERY`, `BUDGET_CHECK`, `DECISION_ADVICE`
4. **Fallback rõ ràng** — khi không hiểu, hỏi lại đúng cách (khắc phục điểm yếu của Moni)

**Không cần cho MVP:** kết nối ngân hàng thật, nhập giao dịch tự động, biểu đồ phức tạp.

---

*Nguyễn Văn Dưỡng · 2A202600967 · Day 05 Lab · 2026-06-03*
