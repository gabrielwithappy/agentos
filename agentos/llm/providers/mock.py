from __future__ import annotations

from collections.abc import Iterator

from agentos.llm.redaction import redact_text
from agentos.llm.types import InvocationRequest, LLMEvent, ProviderCapabilities, ProviderStatus


MOCK_MESSAGE = (
    "Mock response from AgentOS. No real account, token, provider session, "
    "network request, or persistent credential was used."
)


class MockProvider:
    name = "mock"
    mode = "mock"

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(context_aware=True, supports_continuation=False)

    def stream_context(self, request: InvocationRequest) -> Iterator[LLMEvent]:
        """Deterministic multi-turn echo: the response text quotes every
        `user`-role message so tests can verify all prior turns were
        actually passed through, not just the newest prompt. Mirrors
        `stream_once()`'s reasoning/tool_call/tool_result event richness
        (context-aware callers, e.g. the TUI's `ConversationRuntime`, still
        exercise the same process-visualization and `/tools` surfaces)."""
        user_texts = [redact_text(m.text) for m in request.messages if m.role == "user"]
        joined = " | ".join(user_texts) if user_texts else ""
        latest_text = user_texts[-1] if user_texts else ""
        text = f"Received context [{joined}]. {MOCK_MESSAGE}"

        yield LLMEvent(type="start", provider=self.name, mode=self.mode, metadata={"mock": True})
        yield LLMEvent(
            type="reasoning",
            provider=self.name,
            mode=self.mode,
            text="Considering how to respond to the prompt.",
        )
        yield LLMEvent(
            type="tool_call",
            provider=self.name,
            mode=self.mode,
            metadata={"name": "mock_tool", "arguments": {"input": latest_text}},
        )
        yield LLMEvent(
            type="tool_result",
            provider=self.name,
            mode=self.mode,
            metadata={"name": "mock_tool", "summary": "Mock tool executed successfully."},
        )
        yield LLMEvent(
            type="message_delta",
            provider=self.name,
            mode=self.mode,
            text=text,
        )
        yield LLMEvent(
            type="done",
            provider=self.name,
            mode=self.mode,
            usage={
                "input_chars": sum(len(t) for t in user_texts),
                "output_chars": len(text),
            },
        )

    def status(self) -> ProviderStatus:
        return ProviderStatus(
            provider=self.name,
            mode=self.mode,
            credential_present=False,
            authenticated=False,
            persistent_credential=False,
            message=MOCK_MESSAGE,
        )

    def login(self) -> ProviderStatus:
        return self.status()

    def logout(self) -> ProviderStatus:
        return self.status()

    def stream_once(self, prompt: str) -> Iterator[LLMEvent]:
        sanitized_prompt = redact_text(prompt)
        text = f"Received {sanitized_prompt!r}. {MOCK_MESSAGE}"
        yield LLMEvent(
            type="start",
            provider=self.name,
            mode=self.mode,
            metadata={"mock": True},
        )
        yield LLMEvent(
            type="reasoning",
            provider=self.name,
            mode=self.mode,
            text="Considering how to respond to the prompt.",
        )
        yield LLMEvent(
            type="tool_call",
            provider=self.name,
            mode=self.mode,
            metadata={"name": "mock_tool", "arguments": {"input": sanitized_prompt}},
        )
        yield LLMEvent(
            type="tool_result",
            provider=self.name,
            mode=self.mode,
            metadata={"name": "mock_tool", "summary": "Mock tool executed successfully."},
        )
        yield LLMEvent(
            type="message_delta",
            provider=self.name,
            mode=self.mode,
            text=text,
        )
        yield LLMEvent(
            type="done",
            provider=self.name,
            mode=self.mode,
            usage={
                "input_chars": len(sanitized_prompt),
                "output_chars": len(text),
            },
        )
