import { useState } from 'react'
import { Button } from '../ui/Button'
import { Input } from '../ui/Input'

export function OnboardingModal({
  open,
  budget,
  diet,
  note,
  onSave,
  onSkip,
}: {
  open: boolean
  budget: number
  diet: string
  note: string
  onSave: (value: { budget: number; diet: string; note: string }) => void
  onSkip: () => void
}) {
  const [form, setForm] = useState({ budget, diet, note })

  if (!open) return null

  return (
    <div className="modal-backdrop">
      <section className="modal-card">
        <p className="modal-kicker">Setup nhanh</p>
        <h2>Cá nhân hóa Yumi</h2>
        <p>Cho Yumi biết ngân sách, khẩu vị và ghi chú để gợi ý món sát hơn.</p>
        <form
          className="onboarding-form"
          onSubmit={(event) => {
            event.preventDefault()
            onSave(form)
          }}
        >
          <label>
            Ngân sách trung bình
            <select
              className="yumi-select"
              value={String(form.budget)}
              onChange={(event) =>
                setForm((current) => ({ ...current, budget: Number(event.target.value) }))
              }
            >
              <option value="60000">Dưới 60.000đ</option>
              <option value="80000">Dưới 80.000đ</option>
              <option value="120000">Dưới 120.000đ</option>
              <option value="200000">Thoải mái hơn</option>
            </select>
          </label>
          <label>
            Chế độ ăn ưu tiên
            <select
              className="yumi-select"
              value={form.diet}
              onChange={(event) =>
                setForm((current) => ({ ...current, diet: event.target.value }))
              }
            >
              <option value="">Không chọn</option>
              <option value="healthy">Healthy</option>
              <option value="low_cal">Low cal</option>
              <option value="low_carb">Low carb</option>
              <option value="high_protein">High protein</option>
              <option value="vegetarian">Vegetarian</option>
            </select>
          </label>
          <label>
            Ghi chú
            <Input
              value={form.note}
              onChange={(event) =>
                setForm((current) => ({ ...current, note: event.target.value }))
              }
              placeholder="VD: không cay, thích món nước..."
            />
          </label>
          <div className="modal-actions">
            <Button type="button" className="ghost" onClick={onSkip}>
              Bỏ qua
            </Button>
            <Button type="submit">Lưu sở thích</Button>
          </div>
        </form>
      </section>
    </div>
  )
}
