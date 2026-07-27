import os
import sys
import threading
import time
import signal
from unittest.mock import patch
import logging

logging.basicConfig(level=logging.WARNING)

def delayed_sigint():
    time.sleep(1)
    os.kill(os.getpid(), signal.SIGINT)

if __name__ == "__main__":
    os.environ["OBSERVABILITY_ENABLED"] = "1"
    
    # Mock Notifier to print something we can catch
    from agentos.observability.notifier import notifier, DashboardAdapter
    class PrintAdapter(DashboardAdapter):
        async def send_notification(self, payload):
            print(f"NOTIFIED: {payload}")
    notifier.register_adapter(PrintAdapter())

    from agentos.terminal.interaction import run_interactive
    
    t = threading.Thread(target=delayed_sigint)
    t.start()
    
    with patch('builtins.input', side_effect=KeyboardInterrupt):
        run_interactive("mock")
