# Yumi — Product Spec

> Conversational AI Agent cho food delivery: người dùng chỉ cần nói, Yumi lo phần còn lại.

---

## Thông tin team

| Họ tên | MSSV |
|--------|------|
| Lương Đức | 2A202600704 |

---

## Mục lục

1. [Tổng quan sản phẩm](#1-tổng-quan-sản-phẩm)
2. [Vấn đề cần giải quyết](#2-vấn-đề-cần-giải-quyết)
3. [Giải pháp](#3-giải-pháp)
4. [Yêu cầu chức năng](#4-yêu-cầu-chức-năng)
5. [Yêu cầu phi chức năng](#5-yêu-cầu-phi-chức-năng)
6. [Kiến trúc hệ thống](#6-kiến-trúc-hệ-thống)
7. [Thiết kế hội thoại](#7-thiết-kế-hội-thoại)
8. [Phân công team](#8-phân-công-team)
9. [Roadmap & Sprint Plan](#9-roadmap--sprint-plan)
10. [Metrics thành công](#10-metrics-thành-công)

---

## 1. Tổng quan sản phẩm

**Yumi** là một AI ordering copilot được nhúng trong ứng dụng giao đồ ăn.

Thay vì phải tự tìm kiếm, lọc, so sánh rồi thêm từng món vào giỏ, người dùng chỉ cần mô tả nhu cầu bằng ngôn ngữ tự nhiên:

> *"Tối nay ăn gì nhẹ bụng, dưới 80k, giao nhanh, không cay."*

Yumi hiểu ý định, hỏi lại khi cần, đề xuất món phù hợp, và hỗ trợ hoàn tất đơn hàng trong cùng một cuộc hội thoại.

**Tầm nhìn:** Biến trải nghiệm đặt đồ ăn từ *search first* sang *tell first*.

---

## 2. Vấn đề cần giải quyết

### 2.1 Vấn đề người dùng

| Vấn đề | Biểu hiện |
|--------|-----------|
| Không biết ăn gì | Mở app với nhu cầu mơ hồ, phải đối mặt ngay với hàng nghìn lựa chọn |
| Decision fatigue | Quá nhiều lựa chọn → mất động lực → bỏ app |
| Nhiều thao tác | Tìm → lọc → chọn quán → xem menu → thêm giỏ → checkout = 6+ bước |
| Lặp lại nhàm | Khi chọn quá mệt, người dùng đặt đi đặt lại vài món quen, ít khám phá |

### 2.2 Vấn đề doanh nghiệp

- **Conversion thấp**: nhiều người mở app nhưng không hoàn tất đơn
- **Cart abandonment cao**: thêm món rồi bỏ trước khi thanh toán
- **Retention yếu**: trải nghiệm không đủ cá nhân hóa để tạo thói quen
- **Recommendation nông**: "Popular", "Trending" không hiểu bối cảnh từng người

---

## 3. Giải pháp

Yumi đóng vai trò **lớp điều phối quyết định** giữa người dùng và dữ liệu nhà hàng. Hệ thống:

1. **Hiểu ý định** từ ngôn ngữ tự nhiên (tiếng Việt là chính)
2. **Thu thập ngữ cảnh**: thời gian, vị trí, ngân sách, thời tiết, lịch sử, sở thích
3. **Đề xuất có lý do**: không chỉ trả danh sách mà giải thích tại sao phù hợp
4. **Điều phối hành động**: thêm giỏ hàng và hỗ trợ checkout trong cùng cuộc hội thoại

### Các tín hiệu ngữ cảnh Yumi khai thác

- Thời gian trong ngày
- Vị trí hiện tại
- Ngân sách
- Lịch sử đặt hàng
- Sở thích và dị ứng
- Chế độ ăn
- Thời tiết
- Quy mô nhóm

---

## 4. Yêu cầu chức năng

### 4.1 Intents được hỗ trợ (MVP)

| Intent | Ví dụ câu người dùng |
|--------|----------------------|
| `FIND_FOOD` | "Ăn gì giờ?", "Gợi ý món ngon nào" |
| `BY_BUDGET` | "Có gì dưới 80k?", "Ngân sách 50k" |
| `BY_DIET` | "Đang giảm cân", "Có món low carb không?" |
| `BY_WEATHER` | "Trời lạnh quá", "Hôm nay mưa" |
| `BY_GROUP` | "Đặt cho 4 người", "Ăn cùng bạn bè" |
| `BY_TIME` | "Giao dưới 20 phút", "Cần nhanh" |
| `ADD_TO_CART` | "Thêm món đầu tiên", "Lấy cái đó" |
| `VIEW_CART` | "Giỏ hàng của tôi", "Xem lại đơn" |
| `MODIFY_CART` | "Bỏ món phở ra", "Thêm 1 phần nữa" |
| `CHECKOUT` | "Đặt luôn", "Thanh toán" |
| `REORDER` | "Như hôm qua", "Đặt lại đơn trước" |
| `GET_HELP` | "Yumi làm được gì?" |

### 4.2 Các tình huống lỗi cần xử lý

| Tình huống | Cách xử lý |
|------------|------------|
| Cold start (user mới) | Onboarding 3 câu hỏi: khẩu vị, dị ứng, ngân sách |
| Ambiguous query ("Ăn gì cũng được") | Đặt câu hỏi làm rõ ngắn gọn |
| Quán đóng cửa | Fallback sang quán tương đương đang mở |
| API lỗi | Retry có kiểm soát + thông báo thân thiện |
| Recommendation lặp lại | Diversity ranking, xen kẽ món mới |

### 4.3 Luồng đặt hàng tổng quát

```
User nhập → Intent Detection → Entity Extraction
         → Load Context (profile + session + lịch sử)
         → Recommendation Engine → Ranking
         → AI Response (text + suggestion cards)
         → User chọn → Add to Cart → Checkout
```

### 4.4 Yêu cầu cụ thể

**FR-01 — Natural Language Ordering**
Người dùng có thể mô tả nhu cầu bằng tiếng Việt tự nhiên. Hệ thống hiểu và phản hồi phù hợp.

**FR-02 — Context-Aware Recommendations**
Đề xuất dựa trên thời gian, vị trí, thời tiết, lịch sử và sở thích cá nhân.

**FR-03 — Multi-turn Conversation**
Duy trì ngữ cảnh xuyên suốt cuộc hội thoại. Câu sau hiểu được câu trước.

**FR-04 — Cart Management via Chat**
Thêm, sửa, xóa món trong giỏ thông qua tin nhắn.

**FR-05 — Checkout Assistance**
Hỗ trợ chọn địa chỉ, phương thức thanh toán, và xác nhận đơn trong chat.

**FR-06 — Memory & Personalization**
Ghi nhớ sở thích, dị ứng, lịch sử đặt hàng để cá nhân hóa qua các phiên.

**FR-07 — Fallback & Error Handling**
Xử lý mọi trường hợp lỗi một cách thân thiện, không bao giờ bỏ rơi người dùng.

---

## 5. Yêu cầu phi chức năng

| ID | Yêu cầu | Target |
|----|---------|--------|
| NFR-01 | Response time | < 2 giây |
| NFR-02 | Availability | 99.9% uptime |
| NFR-03 | Hallucination rate | < 2% |
| NFR-04 | Concurrent users | 10,000+ |
| NFR-05 | Ngôn ngữ chính | Tiếng Việt |
| NFR-06 | Data compliance | GDPR / PDPA |
| NFR-07 | Intent accuracy | F1 ≥ 0.90 |

---

## 6. Kiến trúc hệ thống

### 6.1 Tech stack

| Layer | Công nghệ |
|-------|-----------|
| Frontend | Next.js + React + Tailwind CSS |
| Backend | FastAPI (Python) |
| Database | PostgreSQL |
| Cache & Session | Redis |
| Vector Search | Qdrant |
| AI | GPT / Claude / Gemini (tuỳ chiến lược) |
| Infrastructure | Docker, AWS ECS / GCP Cloud Run |

### 6.2 Các thành phần AI

```
┌─────────────────────────────────────────────────┐
│                 AI Orchestrator                  │
│                                                  │
│  Intent Detection → Entity Extraction            │
│         ↓                                        │
│  Memory Agent (profile + session + history)      │
│         ↓                                        │
│  Recommendation Agent (candidates)               │
│         ↓                                        │
│  Ranking Agent (relevance × diversity × budget)  │
│         ↓                                        │
│  Cart Agent → Checkout Agent                     │
└─────────────────────────────────────────────────┘
```

**Memory Agent** — Lưu sở thích, dị ứng, lịch sử (PostgreSQL + Redis)

**Recommendation Agent** — Sinh tập ứng viên theo context và intent (Qdrant vector search)

**Ranking Agent** — Sắp xếp theo: relevance × popularity × diversity × budget fit

**Cart Agent** — Chuyển lựa chọn thành giỏ hàng có thể thao tác

**Checkout Agent** — Điều phối bước cuối để hoàn tất đơn hàng

### 6.3 Database schema chính

**users** — id, phone, name, preferred_cuisines, allergies, dietary_goals, avg_budget

**dishes** — id, restaurant_id, name, price, cuisine_tags, diet_tags, calories, is_available

**orders** — id, user_id, status, items (JSONB), total, payment_method, ordered_at

**sessions** — id, user_id, current_intent, conversation_history (JSONB), cart (JSONB)

**feedback** — id, user_id, order_id, rating, comment

### 6.4 Luồng dữ liệu

```
Client → CDN → API Gateway (JWT auth + rate limit)
      → FastAPI → AI Orchestrator
                → PostgreSQL (user data, orders)
                → Redis (session, cart, recent orders)
                → Qdrant (vector search)
                → LLM API (intent + response generation)
```

---

## 7. Thiết kế hội thoại

### 7.1 Nguyên tắc

- **Natural first**: phản hồi như người, không như máy
- **Concise**: không quá 3 gợi ý mỗi lần, không dài dòng
- **Proactive**: hỏi thêm khi cần, không để người dùng đoán
- **Empathetic**: hiểu cảm xúc ("trời mưa", "đang mệt")
- **Graceful fallback**: lỗi thì thông báo thân thiện, không crash hội thoại

### 7.2 Hội thoại mẫu

**Discovery flow**
```
User:  "Ăn gì giờ?"
Yumi:  "Đang 7 giờ tối, trời mát. Bạn muốn ăn nhẹ hay no bụng? 😊"
User:  "No bụng, không quá 100k"
Yumi:  "Có 3 lựa chọn hợp với bạn:
         🍜 Phở bò Hà Nội – 75k (Quán Bà Đặng, giao 20 phút)
         🍱 Cơm gà xối mỡ – 65k (Cơm Ngon, giao 15 phút)
         🥘 Bún bò Huế – 80k (Bún Bò Cô Liên, giao 25 phút)
        Thêm món nào vào giỏ không?"
User:  "Thêm cái thứ 2"
Yumi:  "Đã thêm Cơm gà xối mỡ vào giỏ. Đặt luôn hay cần thêm gì?"
```

**Dietary flow**
```
User:  "Tôi đang giảm cân"
Yumi:  "Hiểu rồi! Bạn ưu tiên low-carb hay high-protein?
        Hoặc cứ để Yumi gợi ý theo calorie thấp cũng được 🥗"
User:  "Calorie thấp thôi"
Yumi:  "3 món dưới 400 kcal gần bạn:
         🥗 Salad cá ngừ – 280 kcal, 55k
         🍳 Ức gà áp chảo rau – 320 kcal, 70k
         🍜 Phở gà không nước béo – 350 kcal, 65k"
```

**Error handling — quán đóng cửa**
```
User:  "Cho tôi bún chả Hương Liên"
Yumi:  "Hương Liên đang đóng cửa tối nay. Mình tìm quán bún chả
        khác gần bạn nhé? Có 2 quán đang mở và đánh giá tốt."
```

### 7.3 Intent routing logic

```
Confidence ≥ 0.85 → Route thẳng
0.60 – 0.85       → Hỏi làm rõ ngắn
< 0.60            → Fallback thân thiện
```

---

## 8. Phân công team

Team 4 người, mỗi người đảm nhận một track độc lập, phối hợp ở các điểm giao nhau.

---

### 👤 Member 1 — Product & AI Design

**Trách nhiệm chính:** Định nghĩa sản phẩm và thiết kế lớp AI

| Hạng mục | Công việc cụ thể |
|----------|-----------------|
| PRD | Viết user stories (15–20 stories), acceptance criteria, MoSCoW prioritization |
| User Journey | Thiết kế journey cho 3 nhóm: New User, Returning User, Group Order |
| Conversation Design | Viết 10+ dialogue mẫu, tone & voice guidelines, error handling dialogues |
| Intent Design | Định nghĩa 12 intents, entity schema, training dataset 500+ câu mẫu |
| Prompt Engineering | System prompt, intent-specific prompts, memory injection templates |
| AI Evaluation | Định nghĩa metrics (Intent F1, NDCG@3, Hallucination rate), test dataset |

**Deliverables:**
- `docs/prd.md` — Product Requirements Document
- `docs/conversation-design.md` — Dialogue flows + tone guidelines
- `data/intent-training-data.json` — Training examples cho intent classifier
- `prompts/` — Thư mục chứa tất cả prompt templates có version control

---

### 👤 Member 2 — AI Engineering & Backend Core

**Trách nhiệm chính:** Xây dựng AI pipeline và backend APIs

| Hạng mục | Công việc cụ thể |
|----------|-----------------|
| AI Orchestrator | Intent detection → entity extraction → context loading → response generation |
| Recommendation Engine | Cold start strategy, personalized ranking, diversity boost |
| Vector Search | Qdrant setup, dish embeddings (384 dims), similarity search |
| Memory System | Short-term (Redis), long-term (PostgreSQL), episodic (recent 10 orders) |
| Backend APIs | `/conversation/message`, `/recommendations`, `/search/dishes`, `/search/restaurants` |
| Tool Calling | `search_menu`, `add_to_cart`, `checkout` tools |

**Deliverables:**
- `backend/app/ai/` — AI Orchestrator, Intent Classifier, Recommendation Engine
- `backend/app/api/conversation.py` — Conversation API endpoint
- `backend/app/api/recommendations.py` — Recommendation API
- `backend/app/services/memory.py` — Memory system (Redis + PostgreSQL + Qdrant)

---

### 👤 Member 3 — Backend & Data

**Trách nhiệm chính:** Database, cart/order flow, backend APIs còn lại

| Hạng mục | Công việc cụ thể |
|----------|-----------------|
| Database | Schema design (8 bảng), migration scripts, indexes, seed data |
| Cart & Order APIs | `/cart/*`, `/orders/*`, `/users/*` |
| Redis Layer | Session store, cart store, episodic memory, cache invalidation |
| Data Pipeline | Batch re-index embeddings (chạy đêm), order history sync |
| Integration | Kết nối weather API, location API |
| Unit Tests | Tests cho cart service, order service, user profile |

**Deliverables:**
- `backend/app/db/` — Models, repositories, migrations
- `backend/app/api/cart.py`, `orders.py`, `users.py`
- `backend/app/services/redis_store.py`
- `tests/unit/` — Unit tests cho backend services

---

### 👤 Member 4 — Frontend & DevOps

**Trách nhiệm chính:** UI chat interface và infrastructure

| Hạng mục | Công việc cụ thể |
|----------|-----------------|
| Chat UI | ChatButton, ChatWindow, MessageList, AIMessage, UserMessage, TypingIndicator |
| Quick Actions | Chips gợi ý ("Ăn gì giờ?", "Gần tôi", "Dưới 80k") |
| Recommendation Cards | Card hiển thị món (ảnh, tên, giá, quán, nút thêm) |
| Cart UI | CartDrawer, CartItem, price breakdown, checkout button |
| Onboarding | 3-step wizard: cuisine → allergy → budget |
| Order Tracking | Status timeline, countdown giao hàng |
| Docker & CI/CD | Dockerfile (backend + frontend), Docker Compose dev, GitHub Actions |
| Monitoring | Prometheus + Grafana dashboards cơ bản |

**Deliverables:**
- `frontend/components/chat/` — Toàn bộ chat UI components
- `frontend/components/cart/` — Cart components
- `frontend/components/onboarding/` — Onboarding wizard
- `docker-compose.yml`, `docker-compose.test.yml`
- `.github/workflows/ci.yml` — CI pipeline

---

### Điểm giao nhau cần phối hợp

| Điểm giao | Member liên quan | Ghi chú |
|-----------|-----------------|---------|
| API contract (request/response schema) | M2 + M3 + M4 | Thống nhất từ Sprint 0 |
| Intent/entity schema | M1 + M2 | M1 define, M2 implement |
| Prompt templates | M1 + M2 | M1 viết, M2 tích hợp |
| Cart state management | M3 + M4 | Backend cart API ↔ Frontend cart UI |
| Conversation state | M2 + M4 | AI response format ↔ Frontend rendering |

---

## 9. Roadmap & Sprint Plan

### Sprint Overview (12 tuần = 6 sprint × 2 tuần)

```
Sprint 0 (W1-2):  Foundation — setup, schema, skeleton
Sprint 1 (W3-4):  Core Chat MVP — user type → Yumi responds
Sprint 2 (W5-6):  Context & Memory — weather, time, history
Sprint 3 (W7-8):  Cart & Checkout — full order flow via chat
Sprint 4 (W9-10): Advanced AI — diversity, less hallucination, clarification
Sprint 5 (W11):   Quality — load test, monitoring, E2E
Sprint 6 (W12):   Launch — UAT, production deploy
```

---

### Sprint 0 — Foundation

**Goal:** Mọi người có thể chạy project local và CI/CD chạy được.

| Task | Owner |
|------|-------|
| Monorepo setup (backend + frontend) | M4 |
| Docker Compose dev environment | M4 |
| GitHub Actions CI skeleton | M4 |
| Database schema + migration scripts | M3 |
| FastAPI app skeleton + health check | M2/M3 |
| Next.js app skeleton | M4 |
| Redis + Qdrant local setup | M2/M3 |
| Seed data (20 restaurants, 100 dishes) | M3 |
| API contract document | All |

---

### Sprint 1 — Core Chat MVP

**Goal:** Người dùng gõ tin nhắn → Yumi trả lời với gợi ý món.

| Task | Owner |
|------|-------|
| System prompt + few-shot prompts | M1 |
| Intent classifier (FIND_FOOD, BY_BUDGET, BY_DIET) | M2 |
| Basic recommendation (popular + budget filter) | M2 |
| POST /conversation/message endpoint | M2 |
| Session management (Redis) | M2/M3 |
| Chat UI: MessageList + UserMessage + AIMessage + ChatInput | M4 |
| QuickActions chips | M4 |
| RecommendationCard component | M4 |
| Unit tests: intent classifier | M2 |

---

### Sprint 2 — Context & Memory

**Goal:** Yumi biết thời gian, thời tiết, lịch sử của bạn.

| Task | Owner |
|------|-------|
| Weather API integration | M3 |
| Time-aware recommendations | M2 |
| User profile CRUD API | M3 |
| Onboarding flow (frontend) | M4 |
| Long-term memory (PostgreSQL) | M2/M3 |
| Episodic memory (recent orders, Redis) | M3 |
| Vector similarity search (Qdrant) | M2 |
| Intent mở rộng: BY_WEATHER, BY_GROUP, BY_TIME | M1/M2 |

---

### Sprint 3 — Cart & Checkout

**Goal:** Người dùng thêm món, sửa giỏ, và đặt đơn trong chat.

| Task | Owner |
|------|-------|
| Cart APIs (add, view, update, remove) | M3 |
| Order creation API | M3 |
| ADD_TO_CART, VIEW_CART, MODIFY_CART, CHECKOUT intents | M1/M2 |
| Tool calling: add_to_cart, checkout | M2 |
| CartDrawer + CartItem UI | M4 |
| Checkout flow UI | M4 |
| Error handling: closed restaurant, out of stock | M2 |
| Integration tests: order flow | M3 |

---

### Sprint 4 — Advanced AI

**Goal:** Hội thoại tự nhiên hơn, ít lặp, ít hallucinate.

| Task | Owner |
|------|-------|
| LLM re-ranking cho recommendations | M2 |
| Diversity boost (tránh recommend toàn Phở) | M2 |
| Clarification questions (ambiguous queries) | M1/M2 |
| Fallback handler (confidence thấp) | M2 |
| Hallucination guardrails (check vs DB) | M2 |
| REORDER intent | M1/M2 |
| A/B testing framework skeleton | M1 |
| Prompt versioning | M1 |

---

### Sprint 5 — Quality

**Goal:** Production-ready.

| Task | Owner |
|------|-------|
| Load testing (Locust) — 1000 concurrent users | M4 |
| E2E tests (Playwright) — 5 happy paths | M3/M4 |
| Prometheus + Grafana dashboards | M4 |
| Alerting rules (latency, hallucination, error rate) | M4 |
| Security audit (JWT, rate limiting, input validation) | M2/M3 |
| Performance optimization (caching, query tuning) | M2/M3 |
| API documentation | M2/M3 |
| Runbook viết (incident response) | M4 |

---

### Sprint 6 — Launch

**Goal:** MVP ra tay người dùng thật.

| Task | Owner |
|------|-------|
| Final QA pass | All |
| Staging deployment | M4 |
| UAT với 10–20 người dùng thật | M1 |
| Bug fixes từ UAT | All |
| Production deployment | M4 |
| Launch monitoring (24h on-call) | All |

---

### Roadmap dài hạn

| Phase | Timeline | Focus |
|-------|----------|-------|
| **MVP** | Q1 (W1–12) | Core chat, 8 intents, cart, checkout, onboarding |
| **Personalization** | Q2 (W13–24) | Collaborative filtering, reorder, learning từ feedback |
| **Cart Automation** | Q3 (W25–36) | Group order, combo, scheduled ordering |
| **Autonomous** | Q4 (W37–48) | Proactive suggestions, predictive ordering |
| **Voice & Expand** | Q5+ | Voice input (tiếng Việt), Zalo Mini App, mở rộng vùng |

---

## 10. Metrics thành công

### Product metrics

| Metric | Baseline | Target Q1 | Target Q3 |
|--------|----------|-----------|-----------|
| Conversion rate | ~22% | 30% | 38% |
| Time-to-order | ~8 phút | 4 phút | 2 phút |
| Cart abandonment | ~40% | 30% | 25% |
| Retention rate | baseline | +10% | +20% |
| Average order value | baseline | flat | +15% |

### AI metrics

| Metric | Target |
|--------|--------|
| Intent classification F1 | ≥ 0.90 |
| Entity extraction F1 | ≥ 0.85 |
| Recommendation NDCG@3 | ≥ 0.80 |
| Hallucination rate | < 2% |
| Clarification success rate | ≥ 80% |
| CSAT (1–5) | ≥ 4.0 |
| Task success rate | ≥ 85% |

---

*Last updated: 2026-06-03 | Team: 4 members | Status: Pre-development*
