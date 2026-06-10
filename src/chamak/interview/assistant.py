from __future__ import annotations

from typing import Any, Protocol

from chamak.llm.base import LLMClient
from chamak.rules.candidates import RuleCandidate


class InterviewAssistant(Protocol):
    """Optional LLM-driven helper for the interview engine."""

    def candidates_from_narrative(self, text: str) -> list[RuleCandidate]: ...
    def suggest_followup(self, context: dict[str, Any]) -> str | None: ...


class NullAssistant:
    def candidates_from_narrative(self, text: str) -> list[RuleCandidate]:
        from chamak.rules.candidates import heuristic_candidates
        return heuristic_candidates(text)

    def suggest_followup(self, context: dict[str, Any]) -> str | None:
        return None


class LLMAssistant:
    def __init__(self, client: LLMClient) -> None:
        self.client = client

    def candidates_from_narrative(self, text: str) -> list[RuleCandidate]:
        from chamak.rules.candidates import candidates as combined
        return combined(text, llm=self.client)

    def suggest_followup(self, context: dict[str, Any]) -> str | None:
        return self.client.next_interview_question(context)


def best_available() -> InterviewAssistant:
    """Pick the most capable assistant the environment supports."""
    try:
        from chamak.llm.openrouter import OpenRouterClient
        client = OpenRouterClient()
        if client.available:
            return LLMAssistant(client)
    except Exception:
        pass
    return NullAssistant()
