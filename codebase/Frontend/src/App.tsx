import { AppShell } from './components/layout/AppShell'
import { ChatWindow } from './components/chat/ChatWindow'
import { CartPanel } from './components/cart/CartPanel'
import { MenuFilters } from './components/menu/MenuFilters'
import { MenuList } from './components/menu/MenuList'
import { MenuSearch } from './components/menu/MenuSearch'
import { OnboardingModal } from './components/onboarding/OnboardingModal'
import { ErrorState } from './components/ui/ErrorState'
import { useAppState } from './hooks/useAppState'
import { useConfig } from './hooks/useConfig'

function App() {
  const {
    sessionId,
    preferences,
    onboardingOpen,
    chat,
    cart,
    menu,
    sendChatMessage,
    addToCartFromChat,
    savePreferences,
    skipOnboarding,
  } = useAppState()

  const config = useConfig()

  if (!sessionId) {
    return <div className="boot-screen">Loading Yumi…</div>
  }

  return (
    <>
      <AppShell
        left={(
          <>
            <section className="brand-card">
              <div className="brand-mark">Y</div>
              <div>
                <h1>Yumi</h1>
                <p>AI ordering copilot</p>
              </div>
            </section>

            <section className="panel-section">
              <p className="section-title">Gợi ý nhanh</p>
              <MenuFilters
                onBudget={(value) => void menu.load({ budget: value })}
                onDiet={(value) => void menu.load({ diet: value })}
                onReset={() => {
                  menu.setFilters({ q: '', budget: null, diet: '' })
                  void menu.load({ q: '', budget: null, diet: '' })
                }}
              />
            </section>

            <section className="panel-section">
              <p className="section-title">Tùy chọn hiện tại</p>
              <div className="mini-stats">
                <div className="stat-card">
                  <span>Ngân sách</span>
                  <strong>{preferences.budget.toLocaleString('vi-VN')}đ</strong>
                </div>
                <div className="stat-card">
                  <span>Diet</span>
                  <strong>{preferences.diet || 'Tất cả'}</strong>
                </div>
              </div>
            </section>

            <section className="panel-section">
              <p className="section-title">Menu mẫu</p>
              <MenuSearch
                value={menu.filters.q}
                onChange={(value) => menu.setFilters((current) => ({ ...current, q: value }))}
                onSubmit={() => void menu.load({ q: menu.filters.q })}
              />
              {menu.error ? <ErrorState>{menu.error}</ErrorState> : null}
              <MenuList
                items={menu.items}
                onAdd={(id) => void cart.addItem(id)}
              />
            </section>
          </>
        )}
        center={(
          <ChatWindow
            messages={chat.messages}
            loading={chat.loading}
            intentLabel={chat.intentLabel}
            onSend={(value) => void sendChatMessage(value)}
            onQuickAction={(value) => void sendChatMessage(value)}
            onReset={chat.resetChat}
            onAddToCart={(id) => void addToCartFromChat(id)}
            config={config}
          />
        )}
        right={(
          <CartPanel
            cart={cart.cart}
            onRemove={(id) => void cart.removeItem(id)}
            onCheckout={() => alert('Demo: đơn hàng đã được tạo thành công.')}
          />
        )}
      />

      <OnboardingModal
        open={onboardingOpen}
        budget={preferences.budget}
        diet={preferences.diet}
        note={preferences.note}
        onSkip={skipOnboarding}
        onSave={savePreferences}
      />
    </>
  )
}

export default App
