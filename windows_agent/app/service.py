import win32serviceutil
import win32service
import win32event
import servicemanager
import asyncio
from .agent import AgentClient
from .logging_setup import setup_logging

class SentinelPiService(win32serviceutil.ServiceFramework):
    _svc_name_ = "SentinelPiEDR"
    _svc_display_name_ = "SentinelPi-EDR Agent"
    _svc_description_ = "SentinelPi-EDR Windows Endpoint Agent"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.agent = AgentClient()

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)

    def SvcDoRun(self):
        setup_logging()
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE, servicemanager.PYS_SERVICE_STARTED, (self._svc_name_, ""))
        asyncio.run(self.agent.start())

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(SentinelPiService)
