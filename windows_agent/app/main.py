import sys
import signal
import threading
import asyncio
from typing import Optional
from PySide6 import QtWidgets, QtCore
from .logging_setup import setup_logging
from .agent import AgentClient
from .ui.app_ui import EnrollmentWindow, TrayApp, StatusWindow

setup_logging()

class AgentThread(threading.Thread):
    def __init__(self, agent: AgentClient):
        super().__init__(daemon=True)
        self.agent = agent

    def run(self) -> None:
        asyncio.run(self.agent.start())


def main() -> None:
    # Allow Ctrl+C to kill the app
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    agent = AgentClient()

    if "--reset" in sys.argv:
        print("Resetting credentials...")
        asyncio.run(agent.disconnect())
        print("Credentials cleared.")

    app = QtWidgets.QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    # Create a timer to wake up the python interpreter every 500ms so it can process signals
    timer = QtCore.QTimer()
    timer.start(500)
    timer.timeout.connect(lambda: None)

    tray = TrayApp(agent, app)
    tray.show()

    # Keep a reference to the enrollment window and thread to prevent GC
    enroll_window: Optional[EnrollmentWindow] = None
    status_window: Optional[StatusWindow] = None
    agent_thread: Optional[AgentThread] = None

    def start_agent():
        print("DEBUG: start_agent called")
        nonlocal agent_thread, status_window
        # Ensure any previous thread is cleaned up if needed (though daemon threads die with the process)
        # In this logic, the previous thread would have exited due to disconnect() setting the stop event.
        print("DEBUG: Creating AgentThread")
        agent_thread = AgentThread(agent)
        print("DEBUG: Starting AgentThread")
        agent_thread.start()
        
        # Show the status window
        print("DEBUG: Creating StatusWindow")
        status_window = StatusWindow(agent)
        status_window.disconnected.connect(on_disconnected)
        print("DEBUG: Showing StatusWindow")
        status_window.show()

    def show_enrollment():
        nonlocal enroll_window
        enroll_window = EnrollmentWindow(agent)
        enroll_window.enrolled.connect(on_enrolled)
        enroll_window.show()

    def on_enrolled():
        print("DEBUG: on_enrolled slot called")
        if enroll_window:
            print("DEBUG: closing enroll_window")
            enroll_window.close()
        print("DEBUG: calling start_agent")
        start_agent()

    def on_disconnected():
        # The agent thread will stop because disconnect() sets the stop event
        show_enrollment()

    tray.disconnected.connect(on_disconnected)

    if not agent.enrolled():
        print("Agent not enrolled. Showing enrollment window.")
        show_enrollment()
    else:
        print("Agent already enrolled. Starting background service.")
        start_agent()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
