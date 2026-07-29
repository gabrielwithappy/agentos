import pytest
import asyncio
import logging
from typing import Any, Dict
from agentos.observability.notifier import DashboardNotifier, DashboardAdapter

class MockAdapter(DashboardAdapter):
    def __init__(self):
        self.received_payloads = []
        
    async def send_notification(self, payload: Dict[str, Any]) -> None:
        self.received_payloads.append(payload)

class FailingAdapter(DashboardAdapter):
    async def send_notification(self, payload: Dict[str, Any]) -> None:
        raise ValueError("Network error!")

def test_notifier_fire_and_forget():
    async def run():
        notifier = DashboardNotifier()
        adapter = MockAdapter()
        notifier.register_adapter(adapter)
        
        payload = {"event": "TASK_STATE_CHANGED", "status": "IN_PROGRESS"}
        
        notifier.notify(payload)
        await asyncio.sleep(0.01)
        
        assert len(adapter.received_payloads) == 1
        assert adapter.received_payloads[0] == payload
    asyncio.run(run())

def test_notifier_error_recovery(caplog):
    async def run():
        notifier = DashboardNotifier()
        adapter = FailingAdapter()
        notifier.register_adapter(adapter)
        
        payload = {"event": "TASK_STATE_CHANGED"}
        
        with caplog.at_level(logging.WARNING):
            notifier.notify(payload)
            await asyncio.sleep(0.01)
        
        assert "API 전송 실패" in caplog.text
        assert "Network error!" in caplog.text
    asyncio.run(run())

def test_notify_and_wait_success():
    notifier = DashboardNotifier()
    adapter = MockAdapter()
    notifier.register_adapter(adapter)
    
    outcomes = notifier.notify_and_wait({"event": "TEST"})
    assert len(outcomes) == 1
    assert outcomes[0].adapter_name == "MockAdapter"
    assert outcomes[0].ok is True
    assert outcomes[0].error is None

def test_notify_and_wait_failure():
    notifier = DashboardNotifier()
    adapter = FailingAdapter()
    notifier.register_adapter(adapter)
    
    outcomes = notifier.notify_and_wait({"event": "TEST"})
    assert len(outcomes) == 1
    assert outcomes[0].adapter_name == "FailingAdapter"
    assert outcomes[0].ok is False
    assert outcomes[0].error == "Network error!"
