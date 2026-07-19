from __future__ import annotations

from collections.abc import Iterator

from agentos.llm.redaction import redact_text
from agentos.llm.types import LLMEvent, ProviderStatus


MOCK_MESSAGE = (
    "Mock response from AgentOS. No real account, token, provider session, "
    "network request, or persistent credential was used."
)


class MockProvider:
    name = "mock"
    mode = "mock"

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
