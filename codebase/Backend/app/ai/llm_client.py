"""
LLM client — two responsibilities:
  1. decide_tool(): tool-calling pass → choose which tool to run
  2. generate_reply(): generation pass → produce natural reply from tool results
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from app.ai.tools import TOOL_DEFINITIONS


# ── Prompts ───────────────────────────────────────────────────────────────────

TOOL_SYSTEM_PROMPT = """
Bạn là Yumi, trợ lý đặt đồ ăn thông minh và thân thiện.
Bạn nói tiếng Việt, ngắn gọn, dùng "bạn/mình".

Luật bắt buộc:
1. Không bịa món, giá, nhà hàng. Món hiển thị phải đến từ menu backend.
2. Nếu người dùng muốn tìm món, hãy gọi tool search_menu.
3. Nếu người dùng muốn thêm món, hãy gọi tool add_to_cart.
4. Nếu người dùng muốn xem giỏ, hãy gọi tool view_cart.
5. Nếu câu mơ hồ, hãy gọi tool clarify với đúng một câu hỏi.
6. Không tự checkout trong MVP.
"""

REPLY_SYSTEM_PROMPT = """
Bạn là Yumi, trợ lý đặt đồ ăn thông minh và thân thiện của người dùng Việt Nam.
Phong cách: thân thiện, ngắn gọn, tự nhiên như người thật. Dùng "bạn/mình".

Quy tắc khi sinh reply:
- Trả lời TRỰC TIẾP vào điều user hỏi — không nói chung chung.
- Đề cập tên món cụ thể từ danh sách gợi ý (nếu có).
- Nếu có dữ liệu thời tiết thực → dùng thông tin đó để giải thích lý do.
- Nếu có kết quả tìm kiếm web → tóm tắt ngắn gọn, trích dẫn nguồn nếu cần.
- Giữ reply NGẮN: 1-3 câu text. Đừng liệt kê lại toàn bộ món.
- Kết thúc bằng một câu mời hành động tiếp theo (thêm giỏ, hỏi thêm...).
- KHÔNG bịa thông tin. Nếu không có dữ liệu → thành thật nói không biết.
"""


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class ToolDecision:
    name: str
    arguments: dict[str, Any]


class LLMUnavailable(Exception):
    pass


# ── Init ──────────────────────────────────────────────────────────────────────

load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)


def _provider() -> str:
    configured = os.getenv("AI_PROVIDER", "").strip().lower()
    if configured:
        return configured
    if os.getenv("GEMINI_API_KEY"):
        return "gemini"
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    return "none"


def has_llm_config() -> bool:
    return _provider() in {"gemini", "openai"}


def provider_mode() -> str:
    provider = _provider()
    if provider == "gemini":
        return "gemini_agent"
    if provider == "openai":
        return "openai_agent"
    return "rule_based_fallback"


# ── Tool decision pass ────────────────────────────────────────────────────────

def decide_tool(message: str, recent_context: list[dict[str, str]] | None = None) -> ToolDecision:
    provider = _provider()
    if provider == "gemini":
        return _decide_tool_gemini(message, recent_context)
    if provider == "openai":
        return _decide_tool_openai(message, recent_context)
    raise LLMUnavailable("No LLM provider configured")


# ── Reply generation pass ─────────────────────────────────────────────────────

def generate_reply(
    user_message: str,
    agent_context: dict[str, Any],
    recent_history: list[dict[str, str]] | None = None,
) -> str:
    """
    Ask the LLM to produce a natural reply given:
    - user_message: what the user said
    - agent_context: collected tool results (suggestions, weather, web, cart, etc.)
    - recent_history: last N turns for multi-turn coherence

    Returns the reply string. Falls back to a simple template on error.
    """
    provider = _provider()
    if provider == "gemini":
        return _generate_reply_gemini(user_message, agent_context, recent_history)
    if provider == "openai":
        return _generate_reply_openai(user_message, agent_context, recent_history)
    raise LLMUnavailable("No LLM provider configured")


def _build_context_prompt(user_message: str, ctx: dict[str, Any]) -> str:
    """Serialize agent_context into a clear text block for the LLM."""
    parts = [f"Câu hỏi của user: {user_message}\n"]

    weather = ctx.get("weather")
    if weather and weather.get("available"):
        parts.append(f"Thời tiết hiện tại: {weather['summary']}")

    suggestions = ctx.get("suggestions", [])
    if suggestions:
        lines = []
        for i, s in enumerate(suggestions[:3], 1):
            open_str = "đang mở" if s.get("is_open") else "đóng"
            delivery = f"{s['delivery_minutes']} phút" if s.get("delivery_minutes") else "?"
            lines.append(
                f"  {i}. {s['name']} — {s['price']:,}đ — {s['restaurant']} ({open_str}, giao {delivery})"
                f"\n     Lý do gợi ý: {s.get('reason', '')}"
            )
        parts.append("Món gợi ý từ menu:\n" + "\n".join(lines))

    web = ctx.get("web_search")
    if web and web.get("available") and web.get("answer"):
        parts.append(f"Kết quả tìm kiếm web: {web['answer']}")

    cart = ctx.get("cart")
    if cart and cart.get("item_count", 0) > 0:
        parts.append(f"Giỏ hàng hiện tại: {cart['item_count']} món, tổng {cart['total']:,}đ")

    # Availability data
    availability = ctx.get("availability")
    if availability:
        parts.append(f"Thông tin quán/món: {availability}")

    # Saved preferences
    prefs = ctx.get("preferences")
    if prefs:
        lines = [f"{k}: {v}" for k, v in prefs.items()]
        parts.append("Sở thích đã lưu:\n" + "\n".join(lines))

    # Added dish (cart action)
    added = ctx.get("added_dish")
    if added:
        parts.append(f"Đã thêm vào giỏ: {added}")

    # Saved preference (save_preference action)
    saved = ctx.get("saved")
    if saved:
        parts.append(f"Vừa lưu sở thích: {saved}")

    intent = ctx.get("intent", "")
    if intent:
        parts.append(f"Intent đã phân loại: {intent}")

    parts.append("\nHãy trả lời tự nhiên, ngắn gọn, đề cập tên món cụ thể nếu có.")
    return "\n\n".join(parts)


def _generate_reply_openai(
    user_message: str,
    agent_context: dict[str, Any],
    recent_history: list[dict[str, str]] | None = None,
) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise LLMUnavailable("OPENAI_API_KEY is not set")

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    context_prompt = _build_context_prompt(user_message, agent_context)

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": REPLY_SYSTEM_PROMPT},
            *(recent_history or [])[-4:],
            {"role": "user", "content": context_prompt},
        ],
        "temperature": 0.7,
        "max_tokens": 300,
    }

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        return payload["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        raise LLMUnavailable(str(exc)) from exc


def _generate_reply_gemini(
    user_message: str,
    agent_context: dict[str, Any],
    recent_history: list[dict[str, str]] | None = None,
) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise LLMUnavailable("GEMINI_API_KEY is not set")

    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    context_prompt = _build_context_prompt(user_message, agent_context)

    contents: list[dict[str, Any]] = []
    for item in (recent_history or [])[-4:]:
        role = "model" if item.get("role") == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": item.get("content", "")}]})
    contents.append({"role": "user", "parts": [{"text": context_prompt}]})

    body = {
        "systemInstruction": {"parts": [{"text": REPLY_SYSTEM_PROMPT}]},
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 300,
        },
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        parts = payload.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        return "".join(p.get("text", "") for p in parts).strip()
    except Exception as exc:
        raise LLMUnavailable(str(exc)) from exc


# ── Tool decision implementations (unchanged logic) ───────────────────────────

def _decide_tool_openai(message: str, recent_context: list[dict[str, str]] | None = None) -> ToolDecision:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise LLMUnavailable("OPENAI_API_KEY is not set")

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": TOOL_SYSTEM_PROMPT},
            *(recent_context or [])[-6:],
            {"role": "user", "content": message},
        ],
        "tools": TOOL_DEFINITIONS,
        "tool_choice": "auto",
        "temperature": 0.1,
    }

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise LLMUnavailable(str(exc)) from exc

    choice = payload["choices"][0]["message"]
    tool_calls = choice.get("tool_calls") or []
    if not tool_calls:
        return ToolDecision(name="clarify", arguments={"question": "Bạn muốn Yumi gợi ý món theo ngân sách, sức khỏe hay bối cảnh hôm nay?"})

    call = tool_calls[0]["function"]
    try:
        arguments = json.loads(call.get("arguments") or "{}")
    except json.JSONDecodeError:
        arguments = {}
    return ToolDecision(name=call["name"], arguments=arguments)


def _gemini_function_declarations() -> list[dict[str, Any]]:
    declarations = []
    for tool in TOOL_DEFINITIONS:
        function = tool["function"]
        parameters = function.get("parameters", {"type": "object", "properties": {}})
        properties = {}
        for name, schema in parameters.get("properties", {}).items():
            schema_type = schema.get("type", "string")
            if isinstance(schema_type, list):
                schema_type = next((item for item in schema_type if item != "null"), "string")
            converted: dict[str, Any] = {
                "type": str(schema_type).upper(),
                "description": schema.get("description", ""),
            }
            enum_vals = [item for item in schema.get("enum", []) if item is not None]
            if enum_vals:
                converted["enum"] = enum_vals
            properties[name] = converted
        declarations.append({
            "name": function["name"],
            "description": function["description"],
            "parameters": {
                "type": "OBJECT",
                "properties": properties,
                "required": parameters.get("required", []),
            },
        })
    return declarations


def _gemini_contents(message: str, recent_context: list[dict[str, str]] | None) -> list[dict[str, Any]]:
    contents: list[dict[str, Any]] = []
    for item in (recent_context or [])[-6:]:
        role = "model" if item.get("role") == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": item.get("content", "")}]})
    contents.append({"role": "user", "parts": [{"text": message}]})
    return contents


def _decide_tool_gemini(message: str, recent_context: list[dict[str, str]] | None = None) -> ToolDecision:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise LLMUnavailable("GEMINI_API_KEY is not set")

    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    body = {
        "systemInstruction": {"parts": [{"text": TOOL_SYSTEM_PROMPT}]},
        "contents": _gemini_contents(message, recent_context),
        "tools": [{"functionDeclarations": _gemini_function_declarations()}],
        "toolConfig": {"functionCallingConfig": {"mode": "AUTO"}},
        "generationConfig": {"temperature": 0.1},
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise LLMUnavailable(str(exc)) from exc

    parts = payload.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    for part in parts:
        function_call = part.get("functionCall")
        if function_call:
            return ToolDecision(
                name=function_call.get("name", "clarify"),
                arguments=function_call.get("args") or {},
            )

    return ToolDecision(
        name="clarify",
        arguments={"question": "Bạn muốn Yumi gợi ý món theo ngân sách, sức khỏe hay bối cảnh hôm nay?"},
    )
