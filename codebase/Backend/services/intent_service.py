class IntentService:
    def detect(self, message: str) -> str:
        text = message.lower().strip()

        if any(keyword in text for keyword in ["giỏ hàng", "xem giỏ", "xem lại đơn", "cart"]):
            return "VIEW_CART"

        if any(keyword in text for keyword in ["thêm", "lấy cái đó", "lấy món", "add"]):
            return "ADD_TO_CART"

        if any(keyword in text for keyword in ["giảm cân", "low carb", "high protein", "healthy", "ăn kiêng", "low cal"]):
            return "BY_DIET"

        if any(keyword in text for keyword in ["dưới", "ngân sách", "budget", "rẻ", "tiền"]):
            return "BY_BUDGET"

        return "FIND_FOOD"
