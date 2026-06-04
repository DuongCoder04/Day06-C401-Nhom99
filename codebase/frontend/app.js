const API_BASE = "http://localhost:8000/api";
const sessionId = localStorage.getItem("yumi_session_id") || crypto.randomUUID();
localStorage.setItem("yumi_session_id", sessionId);

const els = {
  messages: document.querySelector("#messages"),
  form: document.querySelector("#chat-form"),
  input: document.querySelector("#chat-input"),
  menuList: document.querySelector("#menu-list"),
  menuCount: document.querySelector("#menu-count"),
  analyticsPanel: document.querySelector("#analytics-panel"),
  analyticsStatus: document.querySelector("#analytics-status"),
  cartItems: document.querySelector("#cart-items"),
  cartSubtitle: document.querySelector("#cart-subtitle"),
  cartTotal: document.querySelector("#cart-total"),
  checkout: document.querySelector("#checkout-button"),
  toast: document.querySelector("#toast"),
  reset: document.querySelector("#reset-button"),
  onboardingModal: document.querySelector("#onboarding-modal"),
  onboardingForm: document.querySelector("#onboarding-form"),
  onboardingBudget: document.querySelector("#onboarding-budget"),
  onboardingCuisine: document.querySelector("#onboarding-cuisine"),
  onboardingAllergy: document.querySelector("#onboarding-allergy"),
  skipOnboarding: document.querySelector("#skip-onboarding"),
  successModal: document.querySelector("#success-modal"),
  closeSuccess: document.querySelector("#close-success")
};
els.runtime = document.querySelector("#runtime-mode");

function money(value) {
  return `${Number(value).toLocaleString("vi-VN")}đ`;
}

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options
  });
  if (!response.ok) {
    throw new Error(`API error ${response.status}`);
  }
  return response.json();
}

function addMessage(role, text, suggestions = []) {
  const row = document.createElement("div");
  row.className = `row ${role}`;
  const bubble = document.createElement("div");
  bubble.className = `bubble ${role}`;
  bubble.textContent = text;
  row.appendChild(bubble);
  els.messages.appendChild(row);

  if (role === "ai" && suggestions.length) {
    const list = document.createElement("div");
    list.className = "suggestions";
    list.innerHTML = suggestions.map(renderSuggestion).join("");
    bubble.appendChild(list);
  }

  els.messages.scrollTop = els.messages.scrollHeight;
}

function renderSuggestion(dish, index) {
  const openBadge = dish.is_open === false ? `<span class="badge closed">Đang đóng</span>` : `<span class="badge">Đang mở</span>`;
  const deliveryBadge = dish.delivery_minutes ? `<span class="badge">${dish.delivery_minutes} phút</span>` : "";
  const ratingBadge = dish.rating ? `<span class="badge">★ ${dish.rating}</span>` : "";
  const feeBadge = dish.delivery_fee ? `<span class="badge">Ship ${money(dish.delivery_fee)}</span>` : "";
  return `
    <article class="dish-card">
      <img src="${dish.image_url}" alt="${dish.name}">
      <div class="dish-body">
        <h3>${index + 1}. ${dish.name}</h3>
        <div class="dish-meta">
          <span>${dish.restaurant}</span>
          <span class="dish-price">${money(dish.price)}</span>
        </div>
        <div class="dish-badges">${openBadge}${deliveryBadge}${ratingBadge}${feeBadge}</div>
        <p class="dish-reason">${dish.reason}</p>
        <button class="add-button" data-add="${dish.id}" type="button">Thêm</button>
      </div>
    </article>
  `;
}

async function send(message) {
  const text = message.trim();
  if (!text) return;

  addMessage("user", text);
  els.input.value = "";

  try {
    const result = await api("/chat", {
      method: "POST",
      body: JSON.stringify({
        message: text,
        session_id: sessionId,
        user_context: { budget: 80000, diet: "none" }
      })
    });
    addMessage("ai", result.reply, result.suggestions);
    renderCart(result.cart_summary);
    loadAnalytics();
  } catch (error) {
    addMessage("ai", "Backend chưa chạy hoặc API đang lỗi. Hãy chạy FastAPI ở cổng 8000 rồi thử lại.");
  }
}

async function loadAnalytics() {
  try {
    const data = await api("/analytics");
    els.analyticsStatus.textContent = "live";
    els.analyticsPanel.innerHTML = `
      <div class="metric"><strong>${data.total_user_messages}</strong><span>User chat</span></div>
      <div class="metric"><strong>${data.add_to_cart_count}</strong><span>Add cart</span></div>
      <div class="metric"><strong>${data.out_of_scope_count}</strong><span>Out scope</span></div>
      <div class="metric"><strong>${data.preference_count}</strong><span>Memory</span></div>
    `;
  } catch (error) {
    els.analyticsStatus.textContent = "offline";
    els.analyticsPanel.innerHTML = `<div class="metric"><strong>-</strong><span>Chưa có API</span></div>`;
  }
}

async function loadMenu() {
  try {
    const items = await api("/menu");
    els.menuCount.textContent = `${items.length} món`;
    els.menuList.innerHTML = items
      .slice(0, 8)
      .map(
        (dish) => `
          <div class="mini-card">
            <img src="${dish.image_url}" alt="${dish.name}">
            <div>
              <strong>${dish.name}</strong>
              <span>${money(dish.price)} · ${dish.restaurant}</span>
            </div>
          </div>
        `
      )
      .join("");
  } catch (error) {
    els.menuCount.textContent = "API lỗi";
    els.menuList.innerHTML = "<p>Chạy backend ở http://localhost:8000 để tải menu.</p>";
  }
}

async function loadCart() {
  try {
    const cart = await api(`/cart/${sessionId}`);
    renderCart(cart);
  } catch (error) {
    renderCart({ items: [], total: 0, item_count: 0 });
  }
}

async function loadConfig() {
  try {
    const config = await api("/config");
    const labels = {
      gemini_tool_calling: "Yumi dùng Gemini tool calling",
      openai_tool_calling: "Yumi dùng OpenAI tool calling",
      rule_based_fallback: "Yumi dùng rule-based fallback"
    };
    els.runtime.textContent = labels[config.mode] || "Yumi đang sẵn sàng";
  } catch (error) {
    els.runtime.textContent = "Yumi đang chờ backend";
  }
}

function renderCart(cart) {
  els.cartTotal.textContent = money(cart.total || 0);
  els.cartSubtitle.textContent = cart.item_count ? `${cart.item_count} món đã chọn` : "Chưa có món nào";
  els.checkout.disabled = !cart.item_count;

  if (!cart.items || !cart.items.length) {
    els.cartItems.className = "cart-items empty";
    els.cartItems.textContent = "Chọn món từ card gợi ý để thêm vào giỏ.";
    return;
  }

  els.cartItems.className = "cart-items";
  els.cartItems.innerHTML = cart.items
    .map(
      (item) => `
        <div class="cart-item">
          <img src="${item.image_url}" alt="${item.name}">
          <div>
            <strong>${item.name}</strong>
            <span>${money(item.price)} · ${item.restaurant}</span>
          </div>
          <div class="qty">
            <button class="qty-button" data-update="${item.dish_id}" data-delta="-1" type="button">−</button>
            <strong>${item.quantity}</strong>
            <button class="qty-button" data-update="${item.dish_id}" data-delta="1" type="button">+</button>
          </div>
          <button class="remove-button" data-remove="${item.dish_id}" type="button">Xóa</button>
        </div>
      `
    )
    .join("");
}

async function addToCart(dishId) {
  const cart = await api("/cart/add", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, dish_id: dishId, quantity: 1 })
  });
  renderCart(cart);
  showToast("Đã thêm món vào giỏ.");
  loadAnalytics();
}

async function updateCart(dishId, delta) {
  const cart = await api("/cart/update", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, dish_id: dishId, delta })
  });
  renderCart(cart);
}

async function removeCartItem(dishId) {
  const cart = await api("/cart/remove", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, dish_id: dishId })
  });
  renderCart(cart);
  showToast("Đã xóa món khỏi giỏ.");
  loadAnalytics();
}

async function savePreference(key, value) {
  if (!value) return;
  await api("/preferences", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId, preference_key: key, preference_value: String(value) })
  });
}

async function completeOnboarding(event) {
  event?.preventDefault();
  await Promise.all([
    savePreference("budget", els.onboardingBudget.value),
    savePreference("cuisine", els.onboardingCuisine.value),
    savePreference("avoid", els.onboardingAllergy.value.trim())
  ]);
  localStorage.setItem("yumi_onboarding_done", "true");
  els.onboardingModal.classList.add("hidden");
  showToast("Yumi đã lưu sở thích của bạn.");
  loadAnalytics();
}

function skipOnboarding() {
  localStorage.setItem("yumi_onboarding_done", "true");
  els.onboardingModal.classList.add("hidden");
}

function initOnboarding() {
  if (localStorage.getItem("yumi_onboarding_done") === "true") {
    els.onboardingModal.classList.add("hidden");
  }
}

function showToast(text) {
  els.toast.textContent = text;
  els.toast.classList.add("show");
  window.setTimeout(() => els.toast.classList.remove("show"), 2200);
}

function resetChat() {
  els.messages.innerHTML = "";
  addMessage("ai", "Chào bạn, mình là Yumi. Bạn có thể nhắn “Ăn gì giờ?”, “Có gì dưới 80k?” hoặc “Tôi đang giảm cân” để mình gợi ý món phù hợp.");
}

els.form.addEventListener("submit", (event) => {
  event.preventDefault();
  send(els.input.value);
});

document.addEventListener("click", async (event) => {
  const messageButton = event.target.closest("[data-message]");
  if (messageButton) {
    send(messageButton.dataset.message);
  }

  const addButton = event.target.closest("[data-add]");
  if (addButton) {
    await addToCart(addButton.dataset.add);
  }

  const updateButton = event.target.closest("[data-update]");
  if (updateButton) {
    await updateCart(updateButton.dataset.update, Number(updateButton.dataset.delta));
  }

  const removeButton = event.target.closest("[data-remove]");
  if (removeButton) {
    await removeCartItem(removeButton.dataset.remove);
  }
});

els.checkout.addEventListener("click", () => {
  els.successModal.classList.remove("hidden");
  showToast("Demo: đơn hàng đã được tạo thành công.");
});
els.reset.addEventListener("click", resetChat);
els.onboardingForm.addEventListener("submit", completeOnboarding);
els.skipOnboarding.addEventListener("click", skipOnboarding);
els.closeSuccess.addEventListener("click", () => els.successModal.classList.add("hidden"));

initOnboarding();
resetChat();
loadConfig();
loadMenu();
loadCart();
loadAnalytics();
