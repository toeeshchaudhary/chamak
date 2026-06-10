from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Protocol

from chamak.core.errors import LLMError
from chamak.rules.candidates import RuleCandidate

log = logging.getLogger("chamak.llm")


@dataclass
class ChatMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


class LLMClient(Protocol):
    name: str
    available: bool

    def chat(self, messages: list[ChatMessage], *, response_format: str | None = None) -> str: ...
    def extract_rule_candidates(self, text: str) -> list[RuleCandidate]: ...
    def next_interview_question(self, context: dict[str, Any]) -> str | None: ...


def parse_json_object(s: str) -> dict[str, Any]:
    s = s.strip()
    if s.startswith("```"):
        s = s.strip("`")
        if s.startswith("json\n"):
            s = s[5:]
    try:
        return json.loads(s)
    except json.JSONDecodeError as e:
        raise LLMError(f"could not parse JSON from LLM: {e}") from e
