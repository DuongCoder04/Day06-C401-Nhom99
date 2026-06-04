# Dự án: AI Quản Lý Chi Tiêu Theo Ngày

## 1. Evidence pack

**User/pain có thật:**

Người dùng, đặc biệt là sinh viên hoặc người mới đi làm, thường có thu nhập giới hạn theo ngày/tuần/tháng. Vấn đề hay gặp là tiêu lặt vặt nhiều lần trong ngày nhưng không nhận ra tổng tiền đã vượt mức.

**Self-use:**

Bản thân em có thể dùng app này mỗi ngày bằng cách đặt giới hạn, ví dụ:

> Hôm nay chỉ được tiêu 150.000đ.

Sau đó nhập từng khoản:

> Ăn sáng 25.000đ
> Cà phê 30.000đ
> Xăng xe 50.000đ

AI sẽ tính còn bao nhiêu tiền và cảnh báo khi sắp vượt.

**Nguồn ngoài nhóm / kế hoạch lấy nguồn:**

Có thể khảo sát 5–10 bạn sinh viên bằng Google Form với các câu hỏi:

> Bạn có thường vượt ngân sách trong ngày không?
> Bạn có biết hôm nay mình đã tiêu bao nhiêu không?
> Bạn có muốn app cảnh báo trước khi vượt tiền không?
> Trường hợp nào bạn chấp nhận vượt ngân sách?

## 2. Opportunity statement

Nhiều người muốn tiết kiệm tiền nhưng không theo dõi chi tiêu theo thời gian thực. Các app ví điện tử/ngân hàng thường chỉ ghi nhận giao dịch, chưa chủ động “ngăn” người dùng trước khi chi quá tay.

Vì vậy, cơ hội là xây một AI trợ lý giúp người dùng kiểm soát chi tiêu trong ngày, biết số tiền còn lại và chỉ cho phép vượt giới hạn khi có lý do khẩn cấp hợp lý như khám bệnh, mua thuốc, cấp cứu hoặc việc bắt buộc.

## 3. Build slice

**Một user:** Sinh viên muốn kiểm soát tiền tiêu trong ngày.

**Một task:** Kiểm tra một khoản chi mới có được phép tiêu không.

**Một AI decision:** AI quyết định khoản chi là “được phép”, “cảnh báo”, hay “không nên chi/vượt hạn mức”.

**Một output:** Trả về kết quả rõ ràng:

> Được phép chi.
> Sau khoản này bạn còn 40.000đ hôm nay.

Hoặc:

> Không nên chi. Khoản này làm bạn vượt giới hạn 60.000đ và không phải tình huống khẩn cấp.

## 4. Auto/Aug decision

AI **không tự khóa tiền** và không tự chuyển khoản.

AI chỉ:

> Gợi ý, cảnh báo, phân loại khoản chi, đánh giá lý do vượt ngân sách.

Human giữ quyền:

> Người dùng vẫn là người quyết định cuối cùng có tiêu hay không.

Cách chia quyền:

> Nếu khoản chi nằm trong ngân sách: AI cho phép.
> Nếu gần vượt ngân sách: AI cảnh báo.
> Nếu vượt ngân sách: AI hỏi lý do.
> Nếu lý do khẩn cấp: AI cho phép vượt và ghi chú.
> Nếu không khẩn cấp: AI khuyên không nên chi.

## 5. Four paths

### Path 1: Happy path

Người dùng nhập:

> Giới hạn hôm nay: 150.000đ
> Khoản chi: Ăn trưa 45.000đ

AI trả lời:

> Khoản chi hợp lệ. Bạn đã tiêu 45.000đ, còn 105.000đ hôm nay.

### Path 2: Low-confidence path

Người dùng nhập:

> Mua đồ 80.000đ

AI chưa hiểu “mua đồ” là gì nên hỏi lại:

> Bạn có thể nói rõ đây là đồ cần thiết, đồ ăn, học tập hay giải trí không?

### Path 3: Failure path

Người dùng nhập:

> Đi chơi game 200.000đ

Trong khi giới hạn ngày là 150.000đ.

AI trả lời:

> Khoản này vượt ngân sách và không thuộc nhóm khẩn cấp. Bạn không nên chi hôm nay.

### Path 4: Correction path

AI phân loại sai.

Ví dụ người dùng nhập:

> Mua thuốc 120.000đ

AI tưởng là “mua sắm”. Người dùng sửa:

> Đây là thuốc cảm do tôi đang ốm.

AI cập nhật:

> Đã sửa thành nhóm sức khỏe/khẩn cấp. Khoản chi được chấp nhận dù vượt ngân sách.

## 6. Failure mode

**Lỗi nguy hiểm nhất:**

AI đánh giá sai tình huống khẩn cấp, ví dụ người dùng cần khám bệnh thật nhưng AI lại từ chối.

**Cách prototype xử lý:**

AI không được chặn tuyệt đối. AI chỉ đưa khuyến nghị.

Với nhóm sức khỏe, khám bệnh, thuốc men, cấp cứu, tai nạn, sửa xe để đi học/đi làm, AI phải ưu tiên an toàn và cho phép vượt ngân sách.

Thông báo nên viết:

> Đây có vẻ là khoản chi cần thiết. Bạn có thể vượt ngân sách, nhưng hệ thống sẽ ghi nhận đây là khoản khẩn cấp.

## 7. Owner plan

**Research:**
Một người khảo sát người dùng, thu thập pain point, lấy ví dụ chi tiêu thật.

**SPEC:**
Một người viết đặc tả sản phẩm: input, output, rule, flow, edge case.

**Prototype:**
Một người làm web/app đơn giản bằng HTML/CSS/JS hoặc Python Streamlit.
