import os
import json
import urllib.request
import urllib.error


DEFAULT_MODEL = "opencode/deepseek-v4-flash-free"
DEFAULT_ENDPOINT = "https://api.opencode.ai/v1/chat/completions"


def _detect_provider():
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY"):
        return "openai"
    if os.getenv("GEMINI_API_KEY"):
        return "gemini"
    return None


def _openai_chat(messages, model, api_key, endpoint):
    body = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": 4096,
        "temperature": 0.3,
    }).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    return result["choices"][0]["message"]["content"]


def _anthropic_chat(messages, model, api_key):
    system = ""
    msgs = []
    for m in messages:
        if m["role"] == "system":
            system = m["content"]
        else:
            msgs.append(m)
    body = json.dumps({
        "model": model,
        "system": system,
        "messages": msgs,
        "max_tokens": 4096,
        "temperature": 0.3,
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    return result["content"][0]["text"]


def _gemini_chat(messages, model, api_key):
    system = ""
    contents = []
    for m in messages:
        if m["role"] == "system":
            system = m["content"]
        else:
            role = "model" if m["role"] == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": m["content"]}]})
    body = json.dumps({
        "system_instruction": {"parts": [{"text": system}]},
        "contents": contents,
    }).encode("utf-8")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read().decode("utf-8"))
    return result["candidates"][0]["content"]["parts"][0]["text"]


class LLMClient:
    def __init__(self):
        self.provider = _detect_provider()
        self.api_key = (
            os.getenv("LLM_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("ANTHROPIC_API_KEY")
            or os.getenv("GEMINI_API_KEY")
            or ""
        )
        self.model = os.getenv("LLM_MODEL", DEFAULT_MODEL)
        self.endpoint = os.getenv("LLM_ENDPOINT", DEFAULT_ENDPOINT)

    @property
    def available(self):
        return bool(self.api_key)

    def chat(self, messages):
        if not self.api_key:
            raise RuntimeError(
                "No LLM API key configured. "
                "Set LLM_API_KEY (or OPENAI_API_KEY / ANTHROPIC_API_KEY / GEMINI_API_KEY)."
            )
        prov = self.provider or "openai"
        if prov == "anthropic":
            return _anthropic_chat(messages, self.model, self.api_key)
        elif prov == "gemini":
            return _gemini_chat(messages, self.model, self.api_key)
        else:
            return _openai_chat(messages, self.model, self.api_key, self.endpoint)

    def read_skill(self, skill_path: str) -> str:
        if os.path.isfile(skill_path):
            with open(skill_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        return ""
