from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Any

import requests


class GroqError(RuntimeError):
    pass


class GroqHTTPError(GroqError):
    def __init__(self, status_code: int, body: str):
        super().__init__(f"Groq HTTP {status_code}: {body[:400]}")
        self.status_code = status_code
        self.body = body


@dataclass
class GroqClient:
    api_key: str
    base_url: str = "https://api.groq.com/openai/v1"
    timeout_seconds: int = 60
    max_retries: int = 6

    def chat_json(self, *, model: str, system_prompt: str, user_prompt: str, temperature: float = 0.1) -> dict[str, Any]:
        payload = {
            "model": model,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        text = self._chat_raw(payload)
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            extracted = _extract_json_object(text)
            if extracted is not None:
                try:
                    return json.loads(extracted)
                except json.JSONDecodeError:
                    pass
            raise GroqError(f"Model returned non-JSON content: {text[:300]}") from exc

    def list_models(self) -> list[str]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        url = f"{self.base_url}/models"
        resp = requests.get(url, headers=headers, timeout=self.timeout_seconds)
        if resp.status_code >= 400:
            raise GroqError(f"Groq model listing failed HTTP {resp.status_code}: {resp.text[:300]}")
        data = resp.json().get("data", [])
        return [str(m.get("id")) for m in data if m.get("id")]

    def _chat_raw(self, payload: dict[str, Any]) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.base_url}/chat/completions"
        last_err: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = requests.post(url, headers=headers, json=payload, timeout=self.timeout_seconds)
                if resp.status_code >= 400:
                    raise GroqHTTPError(resp.status_code, resp.text)
                body = resp.json()
                choices = body.get("choices", [])
                if not choices:
                    raise GroqError(f"Groq returned no choices: {body}")
                content = choices[0].get("message", {}).get("content", "")
                if not content:
                    raise GroqError("Groq returned empty content")
                return content
            except Exception as exc:
                last_err = exc
                if attempt == self.max_retries:
                    break
                wait = 1.5 * (2 ** (attempt - 1))
                if isinstance(exc, GroqHTTPError) and exc.status_code == 429:
                    retry_after = _extract_retry_after_seconds(exc.body)
                    if retry_after is not None:
                        wait = max(wait, retry_after + 1.0)
                time.sleep(wait)
        raise GroqError(f"Groq request failed after retries: {last_err}")


def _extract_json_object(text: str) -> str | None:
    # Best-effort recovery when the model wraps JSON with prose.
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    candidate = text[start : end + 1]
    # Quick sanity check before expensive parse.
    if not re.search(r'"assignments"|"themes"', candidate):
        return None
    return candidate


def _extract_retry_after_seconds(body: str) -> float | None:
    m = re.search(r"try again in ([0-9.]+)s", body, flags=re.IGNORECASE)
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None

