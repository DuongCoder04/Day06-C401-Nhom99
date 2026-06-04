from app.models.schemas import Entities


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_menu",
            "description": "Tìm món ăn trong menu theo ngân sách, chế độ ăn, bối cảnh hoặc nhóm người.",
            "parameters": {
                "type": "object",
                "properties": {
                    "budget_max": {
                        "type": ["integer", "null"],
                        "description": "Giá tối đa bằng VND, ví dụ 80000.",
                    },
                    "diet_type": {
                        "type": ["string", "null"],
                        "enum": ["low_cal", "high_protein", "vegetarian", None],
                    },
                    "weather": {
                        "type": ["string", "null"],
                        "enum": ["rain", "cold", "hot", None],
                    },
                    "group_size": {
                        "type": ["integer", "null"],
                        "description": "Số người ăn cùng.",
                    },
                    "max_delivery_minutes": {
                        "type": ["integer", "null"],
                        "description": "Thời gian giao tối đa user mong muốn.",
                    },
                },
                "required": ["budget_max", "diet_type", "weather", "group_size", "max_delivery_minutes"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_to_cart",
            "description": "Thêm một món vào giỏ khi người dùng đã chọn rõ món.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dish_ref": {
                        "type": ["string", "null"],
                        "description": "first, second, third hoặc tên món người dùng nhắc đến.",
                    },
                    "quantity": {
                        "type": "integer",
                        "description": "Số lượng cần thêm.",
                        "default": 1,
                    },
                },
                "required": ["dish_ref", "quantity"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "view_cart",
            "description": "Xem giỏ hàng hiện tại.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "clarify",
            "description": "Hỏi lại một câu ngắn khi nhu cầu mơ hồ hoặc thiếu thông tin để hành động.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Câu hỏi làm rõ ngắn gọn bằng tiếng Việt.",
                    }
                },
                "required": ["question"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_user_preference",
            "description": "Lưu sở thích hoặc ràng buộc ăn uống của người dùng cho phiên hiện tại.",
            "parameters": {
                "type": "object",
                "properties": {
                    "preference_key": {
                        "type": "string",
                        "enum": ["budget", "diet", "cuisine", "spice", "avoid", "favorite"],
                    },
                    "preference_value": {
                        "type": "string",
                        "description": "Giá trị preference, ví dụ 80000, japanese, low_cal, không cay.",
                    },
                },
                "required": ["preference_key", "preference_value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_preferences",
            "description": "Đọc sở thích đã lưu của người dùng trong phiên hiện tại.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_availability",
            "description": "Kiểm tra quán của một món hoặc tên quán có đang mở và giao trong bao lâu.",
            "parameters": {
                "type": "object",
                "properties": {
                    "restaurant_or_dish": {
                        "type": "string",
                        "description": "Tên quán hoặc tên món người dùng hỏi.",
                    }
                },
                "required": ["restaurant_or_dish"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recommend_combo",
            "description": "Gợi ý combo món chính và món phụ/đồ uống theo ngân sách hoặc nhóm người.",
            "parameters": {
                "type": "object",
                "properties": {
                    "budget_max": {
                        "type": ["integer", "null"],
                        "description": "Ngân sách tối đa bằng VND.",
                    },
                    "group_size": {
                        "type": ["integer", "null"],
                        "description": "Số người ăn cùng.",
                    },
                },
                "required": ["budget_max", "group_size"],
            },
        },
    },
]


def tool_args_to_entities(args: dict) -> Entities:
    return Entities(
        budget_max=args.get("budget_max"),
        diet_type=args.get("diet_type"),
        weather=args.get("weather"),
        group_size=args.get("group_size"),
        dish_ref=args.get("dish_ref"),
        quantity=args.get("quantity") or 1,
    )
