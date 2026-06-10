from __future__ import annotations

from typing import Any

from chamak.llm.base import ChatMessage
from chamak.rules.candidates import RuleCandidate


class NullClient:
    name = "null"
    available = False

    def chat(self, messages: list[ChatMessage], *, response_format: str | None = None) -> str:
        return ""

    def extract_rule_candidates(self, text: str) -> list[RuleCandidate]:
        return []

    def next_interview_question(self, context: dict[str, Any]) -> str | None:
        return None
