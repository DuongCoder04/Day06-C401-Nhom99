# Yumi: Conversational Ordering for Food Delivery

## 1. Executive Summary

Yumi là một **Conversational AI Agent** được tích hợp trực tiếp vào ứng dụng giao đồ ăn, giúp người dùng chuyển từ việc “tìm kiếm trong biển lựa chọn” sang “ra quyết định thông qua hội thoại”.

Thay vì phải tự mình:
- tìm món
- lọc quán
- so sánh giá
- duyệt menu
- thêm từng món vào giỏ

người dùng chỉ cần mô tả nhu cầu bằng ngôn ngữ tự nhiên như:
> “Tối nay ăn gì nhẹ bụng, dưới 80k, giao nhanh, không cay.”

Hệ thống sẽ:
- hiểu ý định của người dùng
- chủ động hỏi làm rõ khi cần
- khai thác ngữ cảnh phù hợp
- đề xuất món ăn và nhà hàng theo thời gian thực
- hỗ trợ tạo giỏ hàng và đi đến thanh toán

Mục tiêu của Yumi là trở thành **lớp giao diện hội thoại cho trải nghiệm đặt đồ ăn**, nơi người dùng không còn phải “search first”, mà có thể “tell first”.

---

## 2. Problem Statement

### 2.1. User Problem

Trải nghiệm đặt đồ ăn hiện tại thường bị gián đoạn bởi ba vấn đề chính:

**1. Không biết ăn gì**  
Người dùng mở ứng dụng với nhu cầu mơ hồ, nhưng lại phải đối mặt với quá nhiều lựa chọn ngay từ đầu.

**2. Quá tải quyết định**  
Danh sách món ăn, nhà hàng, mức giá, đánh giá và thời gian giao tạo ra hiện tượng *decision fatigue*, khiến người dùng mất động lực ra quyết định.

**3. Tốn nhiều bước thao tác**  
Để đi từ “đói” đến “đặt xong”, người dùng phải đi qua nhiều lớp tương tác: tìm kiếm → lọc → chọn quán → xem menu → thêm giỏ hàng → checkout.

**4. Hành vi lặp lại và thiếu khám phá**  
Khi quá trình ra quyết định quá mệt, người dùng có xu hướng đặt đi đặt lại một vài lựa chọn quen thuộc, dẫn đến trải nghiệm nhàm chán và ít cá nhân hóa.

### 2.2. Business Problem

Với doanh nghiệp vận hành nền tảng giao đồ ăn, các vấn đề trên chuyển hóa thành tác động trực tiếp lên doanh thu:

- **Conversion thấp**: nhiều người mở app nhưng không hoàn tất đơn hàng.
- **Cart abandonment cao**: người dùng thêm món nhưng bỏ dở trước khi thanh toán.
- **Retention thấp**: trải nghiệm không đủ cá nhân hóa để tạo thói quen quay lại.
- **Recommendation hiện tại còn nông**: các nhãn như *Popular*, *Best Seller*, *Trending* hữu ích ở mức bề mặt nhưng chưa thực sự hiểu bối cảnh từng người dùng.

---

## 3. Why This Matters Now

Food delivery đã tối ưu tốt các lớp hạ tầng như:
- logistics
- thanh toán
- mạng lưới nhà hàng
- tốc độ giao hàng

Nhưng lớp **decision-making** vẫn còn rất thô.

Đây chính là khoảng trống để AI tạo ra giá trị mới: không chỉ giúp tìm món nhanh hơn, mà còn giúp người dùng **ra quyết định tốt hơn trong bối cảnh cụ thể**.

Ba xu hướng làm cơ hội này trở nên khả thi hơn:

- **LLM đủ mạnh để hiểu ý định phức tạp** và duy trì hội thoại đa lượt.
- **Cá nhân hóa theo ngữ cảnh** trở thành kỳ vọng mới của người dùng.
- **Conversational commerce** đang dịch chuyển giao diện từ thao tác thủ công sang tương tác ngôn ngữ tự nhiên.

---

## 4. Solution Overview

Yumi là một **AI ordering copilot** được nhúng trong ứng dụng giao đồ ăn, có khả năng hiểu nhu cầu, truy xuất ngữ cảnh, tạo đề xuất phù hợp và hỗ trợ hoàn tất đơn hàng.

### 4.1. Những tín hiệu mà hệ thống có thể tận dụng

- thời gian trong ngày
- vị trí hiện tại
- ngân sách
- lịch sử đặt hàng
- sở thích cá nhân
- chế độ ăn
- thời tiết
- quy mô nhóm
- mục tiêu sức khỏe

### 4.2. Giá trị cốt lõi

Thay vì đưa cho người dùng hàng nghìn lựa chọn, Yumi biến bài toán lựa chọn thành một cuộc hội thoại có hướng dẫn. Hệ thống không chỉ trả về danh sách món, mà còn đóng vai trò như một **lớp điều phối quyết định** giữa nhu cầu người dùng và dữ liệu nhà hàng.

---

## 5. Core User Experience

### Flow tổng quan

User → Yumi → hiểu ý định → thu thập ngữ cảnh → truy xuất món ăn / nhà hàng → xếp hạng → đề xuất → tạo giỏ hàng → thanh toán

### Các tình huống điển hình

**1. Không biết ăn gì**  
Người dùng chỉ cần hỏi: “Ăn gì giờ?”  
Hệ thống sẽ gợi ý theo khẩu vị, ngân sách, thời gian và độ phù hợp hiện tại.

**2. Theo ngân sách**  
“Có gì dưới 80k?”  
Agent ưu tiên món phù hợp budget, đồng thời tối ưu theo mức độ no, phí ship và độ phổ biến.

**3. Theo sức khỏe**  
“Tôi đang giảm cân.”  
Hệ thống chuyển sang bộ tiêu chí khác: high protein, low fat, ít đường, calorie phù hợp.

**4. Theo thời tiết hoặc bối cảnh**  
“Trời mưa”, “Muốn ăn nóng”, “Ăn khuya”  
Agent dùng ngữ cảnh để điều chỉnh đề xuất theo món, thời gian giao và trạng thái quán.

**5. Theo nhóm**  
“Đặt cho 4 người.”  
Hệ thống ưu tiên combo, set menu, món chia sẻ, hoặc gợi ý nhà hàng phù hợp quy mô nhóm.

---

## 6. Intent Coverage

Yumi cần hỗ trợ một nhóm intent trọng tâm sau:

1. **Tìm món ăn**  
   Ví dụ: “Ăn gì giờ?”

2. **Theo ngân sách**  
   Ví dụ: “Có gì dưới 80k?”

3. **Theo sức khỏe / chế độ ăn**  
   Ví dụ: “Tôi đang giảm cân”, “Có món low carb không?”

4. **Theo thời tiết / bối cảnh**  
   Ví dụ: “Trời lạnh quá”, “Hôm nay mưa”

5. **Theo quy mô nhóm**  
   Ví dụ: “Đặt cho 4 người”

6. **Theo thời gian giao**  
   Ví dụ: “Giao dưới 20 phút”

7. **Thêm vào giỏ hàng**  
   Ví dụ: “Thêm món đầu tiên”

8. **Thanh toán / đặt đơn**  
   Ví dụ: “Đặt luôn”

---

## 7. Business Value Hypotheses

Thay vì khẳng định các con số như kết quả đã được chứng minh, nên xem đây là **giả thuyết kinh doanh cần kiểm chứng**.

### 7.1. Với người dùng

- Giảm thời gian ra quyết định từ nhiều phút xuống còn một vài tương tác hội thoại.
- Giảm cảm giác mệt mỏi khi lựa chọn.
- Tăng khả năng khám phá món mới dựa trên bối cảnh thực tế.

### 7.2. Với doanh nghiệp

- Tăng conversion rate nhờ rút ngắn hành trình đặt hàng.
- Giảm cart abandonment nhờ hỗ trợ hội thoại và gợi ý theo ngữ cảnh.
- Tăng retention nhờ cá nhân hóa tốt hơn.
- Tăng AOV bằng cách gợi ý combo, upsell và cross-sell phù hợp.

---

## 8. Failure Modes and Recovery

Một sản phẩm AI tốt không chỉ cần gợi ý hay, mà còn cần xử lý tốt các tình huống thất bại.

### 8.1. Cold Start
Người dùng mới chưa có lịch sử.

**Hướng xử lý:** onboarding nhẹ, hỏi sở thích ban đầu, khai thác tín hiệu ngữ cảnh mặc định.

### 8.2. Ambiguous Query
Người dùng nói mơ hồ như: “Ăn gì cũng được.”

**Hướng xử lý:** đặt câu hỏi làm rõ, ví dụ về khẩu vị, ngân sách hoặc thời gian.

### 8.3. Restaurant Closed
Quán phù hợp nhưng đã đóng cửa hoặc không còn khả dụng.

**Hướng xử lý:** fallback recommendation và ưu tiên nhà hàng tương đương.

### 8.4. API Failure
Một trong các API nguồn dữ liệu bị lỗi hoặc phản hồi chậm.

**Hướng xử lý:** retry có kiểm soát, cache, circuit breaker.

### 8.5. Repetition Loop
Agent liên tục gợi ý cùng một kiểu món.

**Hướng xử lý:** diversity ranking để cân bằng giữa cá nhân hóa và khám phá.

---

## 9. AI Architecture Overview

Kiến trúc AI nên được thiết kế như một lớp điều phối nhiều thành phần, thay vì một prompt đơn lẻ.

### Pipeline đề xuất

Frontend → Agent Layer → Intent Detection → Memory → Recommendation → Ranking → Tool Calling → Restaurant API → Cart API → Checkout API

### Các vai trò chính

**Memory Agent**  
Lưu các tín hiệu dài hạn như sở thích, món ghét, dị ứng, chế độ ăn.

**Recommendation Agent**  
Sinh ra tập ứng viên phù hợp với ngữ cảnh và intent.

**Ranking Agent**  
Xếp hạng lại theo nhiều tiêu chí: cá nhân hóa, thời gian giao, ngân sách, độ đa dạng.

**Cart Agent**  
Chuyển lựa chọn thành giỏ hàng có thể hành động.

**Checkout Agent**  
Điều phối bước cuối để hoàn tất đơn hàng một cách mượt mà.

---

## 10. Suggested Tech Stack

### Frontend
- Next.js
- React

### Backend
- FastAPI

### Data Layer
- PostgreSQL
- Redis
- Qdrant hoặc vector database tương đương

### AI Layer
- LLM: GPT / Claude / Gemini / Llama tùy chiến lược triển khai

Lưu ý: lựa chọn model nên dựa trên chất lượng hội thoại, chi phí suy luận, độ ổn định tool calling và khả năng cá nhân hóa, thay vì chỉ dựa vào tên model.

---

## 11. Monitoring and Success Metrics

### Product Metrics
- Conversion rate
- CTR
- Retention
- Session length
- Cart abandonment rate
- Average order value

### AI Metrics
- Intent accuracy
- Recommendation relevance
- Hallucination rate
- Clarification success rate
- Tool-call success rate

### Nguyên tắc đo lường

Một hệ thống AI chỉ thực sự tốt khi nó không chỉ nói hay, mà còn giúp người dùng **ra quyết định đúng hơn và nhanh hơn**. Vì vậy, các chỉ số sản phẩm và chỉ số AI cần được theo dõi song song.

---

## 12. Roadmap

### Phase 1 — MVP
- hỗ trợ các intent cơ bản
- đề xuất món theo ngân sách và khẩu vị
- hỗ trợ tạo giỏ hàng

### Phase 2 — Personalization
- lưu sở thích người dùng
- học từ lịch sử đặt hàng
- cải thiện ranking theo cá nhân

### Phase 3 — Cart Automation
- hỗ trợ đặt combo
- gợi ý món bổ sung
- giảm số thao tác trước checkout

### Phase 4 — Autonomous Ordering
- hỗ trợ đề xuất gần như hoàn chỉnh theo ngữ cảnh
- tự động chuẩn bị giỏ hàng trước khi người dùng xác nhận

### Phase 5 — Voice Ordering
- mở rộng sang hội thoại giọng nói
- tối ưu cho hands-free ordering

---

## 13. Deployment Concept

Client → Cloudflare → Next.js → FastAPI → Redis → PostgreSQL → Vector DB → LLM

Mục tiêu kiến trúc là giữ cho trải nghiệm đầu cuối nhanh, phần hội thoại linh hoạt, và lớp dữ liệu có khả năng mở rộng để phục vụ cá nhân hóa theo thời gian.

---

## 14. Business Model Options

### 1. SaaS / Platform Licensing
Thu phí theo tháng cho các nền tảng giao đồ ăn muốn tích hợp AI ordering layer.

### 2. Revenue Share
Chia sẻ doanh thu theo mỗi đơn hàng tạo ra từ agent.

### 3. Sponsored Recommendations
Nhà hàng hoặc thương hiệu trả phí để xuất hiện trong các ngữ cảnh phù hợp, với điều kiện không phá vỡ chất lượng đề xuất.

---

## 15. Why Investors Should Care

Food delivery đã tối ưu tốt các bài toán hậu cần, nhưng vẫn để lại một nút thắt lớn ở đầu phễu: **người dùng không biết chọn gì**.

Yumi giải quyết đúng điểm nghẽn đó bằng cách biến thao tác tìm kiếm thành hội thoại ra quyết định.

Nếu được triển khai đúng, đây không chỉ là một chatbot đặt đồ ăn. Đây là một **lớp giao diện AI mới cho thương mại trong ngành food delivery**, nơi người dùng tương tác bằng ngôn ngữ tự nhiên thay vì phải điều hướng qua nhiều lớp filter và menu.

---

## 16. Conclusion

Yumi kết hợp ba năng lực quan trọng:
- hiểu ngữ cảnh
- cá nhân hóa đề xuất
- điều phối hành động đến khi hoàn tất đơn hàng

Đây là một hướng đi có tiềm năng rõ ràng cả về trải nghiệm người dùng lẫn hiệu quả kinh doanh, đồng thời đủ lớn để phát triển thành một nền tảng AI thương mại hóa độc lập.
