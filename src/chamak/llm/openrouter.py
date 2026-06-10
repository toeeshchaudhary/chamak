from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from chamak.config import openrouter_key
from chamak.core.errors import LLMError
from chamak.llm.base import ChatMessage, parse_json_object
from chamak.rules import metrics as metrics_reg
from chamak.rules.candidates import RuleCandidate

log = logging.getLogger("chamak.llm.openrouter")

_DEFAULT_MODEL = "openai/gpt-4o-mini"
_API = "https://openrouter.ai/api/v1/chat/completions"


_EXTRACT_SYS = """You extract investing rule candidates from a user's narrative belief.

Output ONLY a JSON object: {"candidates": [...]} where each candidate has:
  metric, op (one of "<","<=",">",">="), value (number), polarity ("prefer"|"avoid"),
  rationale (short string), confidence (0..1).

`metric` MUST be one of: {metric_keys}.

If the text is too vague to map to any metric, return {"candidates": []}.
Do not invent metrics, units, or thresholds you cannot defend."""


class OpenRouterClient:
    name = "openrouter"

    def __init__(self, *, model: str = _DEFAULT_MODEL, key: str | None = None, timeout: float = 30.0):
        self.model = model
        self._key = key or openrouter_key()
        self.timeout = timeout

    @property
    def available(self) -> bool:
        return bool(self._key)

    def _post(self, payload: dict) -> dict:
        if not self.available:
            raise LLMError("OPENROUTER_API_KEY not set")
        headers = {
            "Authorization": f"Bearer {self._key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/local/chamak",
            "X-Title": "Chamak",
        }
        with httpx.Client(timeout=self.timeout) as client:
            r = client.post(_API, headers=headers, json=payload)
        if r.status_code != 200:
            raise LLMError(f"OpenRouter {r.status_code}: {r.text[:200]}")
        return r.json()

    def chat(self, messages: list[ChatMessage], *, response_format: str | None = None) -> str:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": 0.2,
        }
        if response_format == "json":
            payload["response_format"] = {"type": "json_object"}
        data = self._post(payload)
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            raise LLMError(f"unexpected response shape: {e}") from e

    def extract_rule_candidates(self, text: str) -> list[RuleCandidate]:
        sys = _EXTRACT_SYS.format(metric_keys=", ".join(metrics_reg.keys()))
        msgs = [ChatMessage("system", sys), ChatMessage("user", text)]
        out = self.chat(msgs, response_format="json")
        obj = parse_json_object(out)
        cands_in = obj.get("candidates", [])
        results: list[RuleCandidate] = []
        for c in cands_in:
            try:
                if metrics_reg.get(c["metric"]) is None:
                    continue
                if c["op"] not in ("<", "<=", ">", ">="):
                    continue
                results.append(
                    RuleCandidate(
                        metric=c["metric"],
                        op=c["op"],
                        value=float(c["value"]),
                        polarity=c.get("polarity", "prefer"),
                        rationale=str(c.get("rationale", ""))[:160],
                        confidence=float(c.get("confidence", 0.6)),
                        source="llm",
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue
        return results

    def next_interview_question(self, context: dict[str, Any]) -> str | None:
        sys = (
            "You are the Chamak investor interviewer. You have already collected the "
            "answers below. Suggest ONE next short question (≤120 chars) that would best "
            "refine the investor's reasoning graph. Respond with only the question text."
        )
        usr = json.dumps(context)[:6000]
        try:
            out = self.chat([ChatMessage("system", sys), ChatMessage("user", usr)])
        except LLMError:
            return None
        out = out.strip().splitlines()[0] if out.strip() else ""
        return out or None


def default_client() -> "OpenRouterClient":
    return OpenRouterClient()
