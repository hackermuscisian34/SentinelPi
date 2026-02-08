import sys
import threading
import asyncio
from PySide6 import QtWidgets
from .logging_setup import setup_logging
from .agent import AgentClient
from .ui.app_ui import EnrollmentWindow, TrayApp

setup_logging()

class AgentThread(threading.Thread):
    def __init__(self, agent: AgentClient):
        super().__init__(daemon=True)
        self.agent = agent

    def run(self) -> None:
        asyncio.run(self.agent.start())


def main() -> None:
    agent = AgentClient()
    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    tray = TrayApp(agent, app)
    tray.show()

    def start_agent():
        thread = AgentThread(agent)
        thread.start()

    if not agent.enrolled():
        win = EnrollmentWindow(agent)
        win.enrolled.connect(lambda: (win.close(), start_agent()))
        win.show()
    else:
        start_agent()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
