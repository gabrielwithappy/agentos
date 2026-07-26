from __future__ import annotations

from agentos.llm.prompt import AGENTOS_RESPONSE_STYLE_PROMPT, prepend_response_style
from agentos.llm.types import InvocationMessage


def test_prepend_response_style_puts_prompt_first_and_preserves_order():
    out = prepend_response_style([InvocationMessage(role="system", text="project ctx")])
    assert out[0].text == AGENTOS_RESPONSE_STYLE_PROMPT
    assert out[1].text == "project ctx"


def test_prompt_requires_reporting_actions_and_disclosing_omissions():
    assert "실제로 수행한 행동은 언제나 빠짐없이 보고" in AGENTOS_RESPONSE_STYLE_PROMPT
    assert "생략한 것이 있으면" in AGENTOS_RESPONSE_STYLE_PROMPT


def test_prompt_does_not_override_higher_authority():
    assert "데이터입니다" in AGENTOS_RESPONSE_STYLE_PROMPT
