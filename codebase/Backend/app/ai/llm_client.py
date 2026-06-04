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
Bạn là Yumi, trợ lý đặt đồ ăn thông minh, năng động và thân thiện của người dùng Việt Nam.
Hãy trò chuyện tự nhiên, vui vẻ như một người bạn thực sự đang tư vấn ăn uống.
Xưng hô thân mật: "mình" - "bạn".

Hướng dẫn hội thoại để văn phong tự nhiên:
1. Trả lời trực tiếp và ngắn gọn vào câu hỏi (khoảng 2-3 câu). Tránh văn phong rập khuôn, hành chính.
2. Giới thiệu món ăn kèm theo tính từ gợi cảm giác ngon miệng và lý do thuyết phục (ví dụ: ấm nóng ngày mưa, nhẹ bụng giữ dáng, mát lạnh sảng khoái). Tránh liệt kê khô khan.
3. Điều chỉnh linh hoạt số lượng món giới thiệu dựa trên ngữ cảnh:
   - Nếu user hỏi cụ thể 1 món/quán: Tập trung mô tả chi tiết món/quán đó, tuyệt đối không liệt kê các món khác ngoài lề.
   - Nếu user nhờ gợi ý chung chung hoặc tìm món: Đưa ra 2-3 lựa chọn khác nhau từ menu gợi ý để họ lựa chọn.
4. Tích hợp thời tiết hoặc ngân sách một cách tinh tế nếu có trong ngữ cảnh. Không lặp đi lặp lại cùng một câu thời tiết ở các lượt hội thoại kế tiếp nhau.
5. Luôn kết thúc bằng một câu hỏi gợi mở tự nhiên để hỗ trợ họ đặt hàng (thêm vào giỏ, xem menu, chốt đơn).

Ví dụ phản hồi tốt:
User: "Trời mưa lạnh thế này ăn gì ngon mình ơi?"
Yumi: "Mưa lạnh thế này thì làm một tô Bún bò Huế nóng hổi, cay tê là chuẩn bài nhất luôn bạn ơi! Mình gợi ý quán Bún Bò Cô Liên đang mở cửa gần bạn nè, bạn có muốn thêm món này vào giỏ hàng luôn không?"
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


def _build_context_prompt(ctx: dict[str, Any]) -> str:
    """Serialize agent_context into a structured metadata block for the LLM."""
    parts = ["[SYSTEM METADATA - THÔNG TIN NGỮ CẢNH ĐỂ TRẢ LỜI]"]

    weather = ctx.get("weather")
    if weather and weather.get("available"):
        parts.append(f"- Thời tiết hiện tại: {weather['summary']}")

    web = ctx.get("web_search")
    has_web_answer = web and web.get("available") and web.get("answer")
    if has_web_answer:
        parts.append(f"- Kết quả tìm kiếm web (ưu tiên sử dụng thông tin này): {web['answer']}")
        if web.get("results"):
            for r in web["results"][:2]:
                parts.append(f"  * {r['title']}: {r['content'][:150]}")

    suggestions = ctx.get("suggestions", [])
    if suggestions and not has_web_answer:
        lines = []
        seen_names = set()
        for i, s in enumerate(suggestions[:3], 1):
            name = s.get("name", "")
            if name in seen_names:
                continue
            seen_names.add(name)
            open_str = "đang mở" if s.get("is_open") else "đóng"
            delivery = f"{s['delivery_minutes']} phút" if s.get("delivery_minutes") else "?"
            lines.append(
                f"  {i}. {s['name']} — {s['price']:,}đ — {s['restaurant']} ({open_str}, giao {delivery})"
                f"\n     Lý do: {s.get('reason', '')}"
            )
        if lines:
            parts.append("- Món ăn gợi ý từ menu:\n" + "\n".join(lines))
    elif suggestions and has_web_answer:
        top = suggestions[0]
        parts.append(
            f"- Món ăn trong menu: {top.get('name')} ({top.get('price', 0):,}đ) — "
            f"có thể gợi ý kèm nếu phù hợp."
        )

    cart = ctx.get("cart")
    if cart and cart.get("item_count", 0) > 0:
        parts.append(f"- Giỏ hàng hiện tại: {cart['item_count']} món, tổng {cart['total']:,}đ")

    availability = ctx.get("availability")
    if availability:
        parts.append(f"- Thông tin quán/món: {availability}")

    prefs = ctx.get("preferences")
    if prefs:
        lines = [f"  * {k}: {v}" for k, v in prefs.items()]
        parts.append("- Sở thích đã lưu:\n" + "\n".join(lines))

    added = ctx.get("added_dish")
    if added:
        parts.append(f"- Đã thêm vào giỏ: {added}")

    saved = ctx.get("saved")
    if saved:
        parts.append(f"- Vừa lưu sở thích: {saved}")

    intent = ctx.get("intent", "")
    if intent:
        parts.append(f"- Intent: {intent}")

    return "\n".join(parts)


def _generate_reply_openai(
    user_message: str,
    agent_context: dict[str, Any],
    recent_history: list[dict[str, str]] | None = None,
) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise LLMUnavailable("OPENAI_API_KEY is not set")

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    context_prompt = _build_context_prompt(agent_context)
    final_user_content = f"{context_prompt}\n\nTin nhắn thực tế từ người dùng: {user_message}"

    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": REPLY_SYSTEM_PROMPT},
            *(recent_history or [])[-4:],
            {"role": "user", "content": final_user_content},
        ],
        "temperature": 0.7,
        "max_tokens": 512,
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

    context_prompt = _build_context_prompt(agent_context)
    final_user_content = f"{context_prompt}\n\nTin nhắn thực tế từ người dùng: {user_message}"

    contents: list[dict[str, Any]] = []
    for item in (recent_history or [])[-4:]:
        role = "model" if item.get("role") == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": item.get("content", "")}]})
    contents.append({"role": "user", "parts": [{"text": final_user_content}]})

    body = {
        "systemInstruction": {"parts": [{"text": REPLY_SYSTEM_PROMPT}]},
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 800,
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
        text = "".join(p.get("text", "") for p in parts).strip()
        # Guard against truncated replies (Gemini may cut mid-sentence on token limit)
        if text and not text[-1] in ".!?…\"'":
            # Find the last complete sentence
            for end_char in (".", "!", "?", "…"):
                last = text.rfind(end_char)
                if last > len(text) // 2:  # only trim if not cutting too much
                    text = text[: last + 1]
                    break
        return text or ""
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
