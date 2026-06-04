import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.ai.tools import TOOL_DEFINITIONS


SYSTEM_PROMPT = """
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


@dataclass
class ToolDecision:
    name: str
    arguments: dict[str, Any]


class LLMUnavailable(Exception):
    pass


def _load_local_env() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_local_env()


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


def decide_tool(message: str, recent_context: list[dict[str, str]] | None = None) -> ToolDecision:
    provider = _provider()
    if provider == "gemini":
        return _decide_tool_gemini(message, recent_context)
    if provider == "openai":
        return _decide_tool_openai(message, recent_context)
    raise LLMUnavailable("No LLM provider configured")


def _decide_tool_openai(message: str, recent_context: list[dict[str, str]] | None = None) -> ToolDecision:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise LLMUnavailable("OPENAI_API_KEY is not set")

    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            *(recent_context or [])[-6:],
            {"role": "user", "content": message},
        ],
        "tools": TOOL_DEFINITIONS,
        "tool_choice": "auto",
        "temperature": 0.1,
    }

    request = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
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
            enum = [item for item in schema.get("enum", []) if item is not None]
            if enum:
                converted["enum"] = enum
            properties[name] = converted

        declarations.append(
            {
                "name": function["name"],
                "description": function["description"],
                "parameters": {
                    "type": "OBJECT",
                    "properties": properties,
                    "required": parameters.get("required", []),
                },
            }
        )
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
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": _gemini_contents(message, recent_context),
        "tools": [{"functionDeclarations": _gemini_function_declarations()}],
        "toolConfig": {"functionCallingConfig": {"mode": "AUTO"}},
        "generationConfig": {"temperature": 0.1},
    }

    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
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


def provider_mode() -> str:
    provider = _provider()
    if provider == "gemini":
        return "gemini_tool_calling"
    if provider == "openai":
        return "openai_tool_calling"
    return "rule_based_fallback"
