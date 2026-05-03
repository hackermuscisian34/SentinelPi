import win32serviceutil  # type: ignore
import win32service  # type: ignore
import win32event  # type: ignore
import servicemanager  # type: ignore
import asyncio
import logging
from .agent import AgentClient
from .logging_setup import setup_logging

logger = logging.getLogger("agent.service")

class SentinelPiService(win32serviceutil.ServiceFramework):
    _svc_name_ = "SentinelPiEDR"
    _svc_display_name_ = "SentinelPi-EDR Agent"
    _svc_description_ = "SentinelPi-EDR Windows Endpoint Agent"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.agent = None
        self.loop = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        if self.loop and self.agent:
            try:
                asyncio.run_coroutine_threadsafe(self.agent.stop(), self.loop)
            except Exception:
                pass

    def SvcDoRun(self):
        setup_logging()
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, servicemanager.PYS_SERVICE_STARTED, (self._svc_name_, ""))

        try:
            self.agent = AgentClient()
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self.agent.start())
        except Exception as e:
            logger.error(f"Service error: {e}")
            servicemanager.LogMsg(servicemanager.EVENTLOG_ERROR_TYPE, servicemanager.PYS_SERVICE_STOPPED, (self._svc_name_, str(e)))
        finally:
            if self.loop:
                self.loop.close()

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(SentinelPiService)
