# Yumi — Lab Plan (1 ngày)

> Bài lab 1 ngày · Team 4 người · Core: AI conversational ordering

---

## Mục tiêu cuối ngày

Demo được flow này:

```
User gõ tin nhắn → Yumi hiểu ý định → Gợi ý món ăn phù hợp → User thêm vào giỏ → Xem giỏ hàng
```

**Không cần:** thanh toán thật, xác thực user, database phức tạp, deploy production.

---

## Scope cắt gọn

| Giữ lại ✅ | Bỏ qua ❌ |
|-----------|---------|
| Chat interface (FE) | Auth / đăng nhập |
| AI intent detection | Thanh toán thật |
| AI gợi ý món theo ngữ cảnh | Order tracking |
| Giỏ hàng đơn giản (thêm/xem) | Vector DB (Qdrant) |
| Mock menu data (JSON) | CI/CD, Docker |
| FastAPI backend | Monitoring, logging |
| 4–5 intents cơ bản | Voice, đa ngôn ngữ |

---

## Tech stack tối giản

| Layer | Công nghệ |
|-------|-----------|
| Frontend | Next.js + Tailwind CSS |
| Backend | FastAPI (Python) |
| AI | OpenAI GPT-4o-mini (hoặc Claude) |
| Data | JSON file (mock menu) hoặc SQLite |
| Session | In-memory (dict Python) |

---

## Phân công 4 người

---

### 👤 Member 1 — AI Engineer (Backend AI)

**Nhiệm vụ:** Xây dựng lớp AI — trái tim của Yumi

**Công việc:**

1. Viết system prompt cho Yumi
   - Persona: thân thiện, nói tiếng Việt, chuyên gợi ý đồ ăn
   - Rules: không bịa món, hỏi lại khi mơ hồ, tối đa 3 gợi ý mỗi lần

2. Xây dựng Intent Classifier
   - Nhận message → gọi LLM → trả về `{ intent, entities }`
   - 5 intents: `FIND_FOOD`, `BY_BUDGET`, `BY_DIET`, `ADD_TO_CART`, `VIEW_CART`

3. Xây dựng Recommendation Logic
   - Filter món từ mock menu theo budget, diet, keyword
   - Trả về top 3 gợi ý

4. Viết API endpoint chính:
   - `POST /chat` — nhận message, trả reply + suggestions

**Files:**
```
backend/
├── ai/
│   ├── intent_classifier.py   ← gọi LLM classify intent
│   ├── recommender.py         ← filter + rank món
│   └── prompts.py             ← system prompt + templates
└── api/
    └── chat.py                ← POST /chat endpoint
```

---

### 👤 Member 2 — Backend Engineer

**Nhiệm vụ:** API server, dữ liệu, giỏ hàng

**Công việc:**

1. Setup FastAPI project (main.py, CORS, router)

2. Mock menu data (`data/menu.json`)
   - 15–20 món với: id, name, price, category, tags (diet, cuisine), restaurant

3. Cart APIs:
   - `POST /cart/add` — thêm món vào giỏ (lưu in-memory theo session_id)
   - `GET /cart/{session_id}` — xem giỏ hàng
   - `DELETE /cart/remove` — xóa món (bonus)

4. Menu APIs:
   - `GET /menu` — lấy toàn bộ menu
   - `GET /menu/search?q=&budget=&diet=` — tìm kiếm

5. Session management đơn giản (Python dict, không cần Redis)

**Files:**
```
backend/
├── main.py                    ← FastAPI app, CORS setup
├── data/
│   └── menu.json              ← mock menu data
├── api/
│   ├── cart.py                ← cart endpoints
│   └── menu.py                ← menu endpoints
└── services/
    └── cart_service.py        ← in-memory cart logic
```

---

### 👤 Member 3 — Frontend (Chat UI)

**Nhiệm vụ:** Giao diện chat chính

**Công việc:**

1. Layout tổng thể: sidebar trái (menu/cart) + chat chính ở giữa

2. Chat components:
   - `ChatWindow` — khung chat chính
   - `MessageList` — danh sách tin nhắn
   - `UserMessage` — bubble tin nhắn user (bên phải)
   - `AIMessage` — bubble tin nhắn Yumi (bên trái, có avatar)
   - `ChatInput` — input + nút gửi
   - `TypingIndicator` — "Yumi đang trả lời..."

3. Quick action chips:
   - "Ăn gì giờ?", "Dưới 80k", "Đang giảm cân", "Gợi ý hôm nay"

4. Recommendation Cards (hiển thị trong tin nhắn AI):
   - Ảnh, tên món, giá, tên quán, nút "Thêm vào giỏ"

5. Kết nối API: gọi `POST /chat` khi user gửi tin

**Files:**
```
frontend/
├── components/
│   ├── chat/
│   │   ├── ChatWindow.tsx
│   │   ├── MessageList.tsx
│   │   ├── UserMessage.tsx
│   │   ├── AIMessage.tsx
│   │   ├── ChatInput.tsx
│   │   └── TypingIndicator.tsx
│   └── RecommendationCard.tsx
├── hooks/
│   └── useChat.ts             ← state + API calls
└── app/
    └── page.tsx               ← main layout
```

---

### 👤 Member 4 — Frontend (Cart + Integration)

**Nhiệm vụ:** Giỏ hàng, onboarding, kết nối toàn bộ

**Công việc:**

1. Cart UI:
   - `CartPanel` — panel bên phải hoặc drawer
   - `CartItem` — hiển thị từng món (tên, giá, số lượng)
   - Tổng tiền
   - Nút "Đặt hàng" (chỉ hiện toast "Đặt thành công!" là đủ)

2. Onboarding đơn giản:
   - Modal lần đầu mở app: hỏi 2 câu — khẩu vị yêu thích + ngân sách trung bình
   - Lưu vào localStorage, inject vào context khi gọi `/chat`

3. Integration giữa Chat và Cart:
   - Khi AI suggest món → nút "Thêm" trong RecommendationCard gọi `POST /cart/add`
   - CartPanel tự cập nhật

4. API service layer:
   - `lib/api.ts` — tập trung tất cả fetch calls (chat, cart, menu)

5. Responsive + polish UI nhỏ nếu còn thời gian

**Files:**
```
frontend/
├── components/
│   └── cart/
│       ├── CartPanel.tsx
│       └── CartItem.tsx
├── lib/
│   └── api.ts                 ← tất cả API calls
├── context/
│   └── CartContext.tsx        ← global cart state
└── components/
    └── OnboardingModal.tsx
```

---

## Timeline gợi ý (8 tiếng)

| Giờ | Mốc |
|-----|-----|
| 0:00 – 0:30 | Kickoff: thống nhất API contract (request/response format) |
| 0:30 – 3:00 | Build song song theo track |
| 3:00 – 3:30 | **Checkpoint 1**: BE `/chat` chạy được, FE chat UI render được |
| 3:30 – 5:30 | Tiếp tục build + integrate |
| 5:30 – 6:00 | **Checkpoint 2**: Chat + Cart chạy end-to-end |
| 6:00 – 7:00 | Polish, fix bugs, chuẩn bị demo |
| 7:00 – 8:00 | Demo + buffer |

---

## API Contract (thống nhất từ đầu)

### POST /chat
```json
// Request
{
  "message": "Ăn gì giờ nhỉ?",
  "session_id": "abc123",
  "user_context": {
    "budget": 80000,
    "diet": "none"
  }
}

// Response
{
  "reply": "Tối nay Yumi gợi ý 3 món này cho bạn 😊",
  "intent": "FIND_FOOD",
  "suggestions": [
    {
      "id": "dish_01",
      "name": "Phở bò tái",
      "price": 65000,
      "restaurant": "Phở Hà Nội",
      "tags": ["beef", "noodle"],
      "image_url": "/images/pho.jpg"
    }
  ]
}
```

### POST /cart/add
```json
// Request
{ "session_id": "abc123", "dish_id": "dish_01", "quantity": 1 }

// Response
{ "success": true, "cart_total": 65000, "item_count": 1 }
```

### GET /cart/{session_id}
```json
// Response
{
  "items": [
    { "dish_id": "dish_01", "name": "Phở bò tái", "price": 65000, "quantity": 1 }
  ],
  "total": 65000
}
```

---

## Điểm giao nhau cần nói chuyện ngay từ đầu

| Vấn đề | Quyết định |
|--------|-----------|
| session_id | FE tự generate (UUID) khi load page, gửi kèm mọi request |
| Suggestions format | M1 (BE AI) define, M3/M4 (FE) implement theo |
| Image món ăn | Dùng placeholder hoặc Unsplash URL trong mock data |
| Port | Backend: `localhost:8000`, Frontend: `localhost:3000` |
| CORS | M2 setup `allow_origins=["http://localhost:3000"]` |

---

*Lab Day · Yumi · Team 4 · 2026-06-03*
