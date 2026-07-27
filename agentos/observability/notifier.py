import asyncio
import logging
from typing import Any, Dict, Protocol, List

logger = logging.getLogger(__name__)

class DashboardAdapter(Protocol):
    async def send_notification(self, payload: Dict[str, Any]) -> None:
        """Send notification to the external dashboard."""
        ...

class DashboardNotifier:
    def __init__(self) -> None:
        self._adapters: List[DashboardAdapter] = []
        self._background_tasks: set[asyncio.Task] = set()

    def register_adapter(self, adapter: DashboardAdapter) -> None:
        self._adapters.append(adapter)

    def clear_adapters(self) -> None:
        self._adapters.clear()

    def notify(self, payload: Dict[str, Any]) -> None:
        """
        Notify all registered adapters in a fire-and-forget manner.
        Does not block the main execution.
        """
        for adapter in self._adapters:
            try:
                loop = asyncio.get_running_loop()
                task = loop.create_task(self._safe_send(adapter, payload))
                self._background_tasks.add(task)
                task.add_done_callback(self._background_tasks.discard)
            except RuntimeError:
                import threading
                def _run_in_thread():
                    asyncio.run(self._safe_send(adapter, payload))
                thread = threading.Thread(target=_run_in_thread, daemon=True)
                thread.start()

    async def _safe_send(self, adapter: DashboardAdapter, payload: Dict[str, Any]) -> None:
        """Safely send notification, catching and logging any errors to prevent crashes."""
        try:
            await adapter.send_notification(payload)
        except Exception as e:
            logger.warning(f"[Observability Warning] API 전송 실패: ({type(e).__name__}) {str(e)}")

# Global singleton instance
notifier = DashboardNotifier()
