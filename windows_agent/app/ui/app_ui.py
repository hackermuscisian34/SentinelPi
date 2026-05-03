import asyncio
from PySide6 import QtWidgets, QtCore
from ..agent import AgentClient

class EnrollmentWindow(QtWidgets.QWidget):
    enrolled = QtCore.Signal()

    def __init__(self, agent: AgentClient) -> None:
        super().__init__()
        self.agent = agent
        self.setWindowTitle("SentinelPi-EDR Enrollment")
        self.setFixedSize(420, 260)
        self.setStyleSheet(
            "background-color: #f4fff7; color: #1b2b21; font-family: 'Segoe UI';"
        )

        layout = QtWidgets.QVBoxLayout()
        title = QtWidgets.QLabel("SentinelPi-EDR Enrollment")
        title.setStyleSheet("font-size: 20px; font-weight: 700; color: #1b2b21;")
        layout.addWidget(title)

        self.pi_ip = QtWidgets.QLineEdit()
        self.pi_ip.setPlaceholderText("Raspberry Pi IP (e.g., 192.168.1.10)")
        self.pi_ip.setStyleSheet("background: #ffffff; border: 1px solid #d2e6d9; padding: 8px;")
        self.pairing = QtWidgets.QLineEdit()
        self.pairing.setPlaceholderText("Pairing code")
        self.pairing.setMaxLength(12)
        self.pairing.setStyleSheet("background: #ffffff; border: 1px solid #d2e6d9; padding: 8px;")

        self.status = QtWidgets.QLabel("")
        self.status.setStyleSheet("color: #2f6f2f; font-weight: 600;")

        btn = QtWidgets.QPushButton("Enroll")
        btn.setStyleSheet(
            "background-color: #2f7d4c; color: white; padding: 10px; border-radius: 6px; font-weight: 600;"
        )
        btn.clicked.connect(self._enroll)

        layout.addWidget(self.pi_ip)
        layout.addWidget(self.pairing)
        layout.addWidget(btn)
        layout.addWidget(self.status)
        self.setLayout(layout)

    def _enroll(self) -> None:
        print("DEBUG: _enroll called")
        try:
            print(f"DEBUG: calling self.agent.enroll with IP={self.pi_ip.text().strip()}")
            data = self.agent.enroll(self.pi_ip.text().strip(), self.pairing.text().strip())
            print("DEBUG: enroll returned data:", data)
            self.status.setText("Enrollment successful")
            print("DEBUG: Emitting enrolled signal")
            self.enrolled.emit()
            print("DEBUG: Signal emitted")
        except Exception as exc:
            print(f"DEBUG: Exception in _enroll: {exc}")
            import traceback
            traceback.print_exc()
            self.status.setStyleSheet("color: #b00020;")
            self.status.setText(str(exc))

class StatusWindow(QtWidgets.QWidget):
    disconnected = QtCore.Signal()

    def __init__(self, agent: AgentClient) -> None:
        super().__init__()
        self.agent = agent
        self.setWindowTitle("SentinelPi-EDR Status")
        self.setFixedSize(300, 150)
        self.setStyleSheet(
            "background-color: #f4fff7; color: #1b2b21; font-family: 'Segoe UI';"
        )

        layout = QtWidgets.QVBoxLayout()
        title = QtWidgets.QLabel("SentinelPi Agent")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #1b2b21;")
        layout.addWidget(title)
        
        status = QtWidgets.QLabel("Status: Connected & Protected")
        status.setStyleSheet("color: #2f7d4c; font-weight: 600; margin-bottom: 20px;")
        layout.addWidget(status)

        disconnect_btn = QtWidgets.QPushButton("Disconnect / Unenroll")
        disconnect_btn.setStyleSheet(
            "background-color: #b00020; color: white; padding: 8px; border-radius: 6px; font-weight: 600;"
        )
        disconnect_btn.clicked.connect(self._disconnect)
        layout.addWidget(disconnect_btn)
        
        self.setLayout(layout)

        # Check enrollment status every 2 seconds
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._check_enrollment)
        self.timer.start(2000)
    
    def _check_enrollment(self) -> None:
        if not self.agent.enrolled():
            print("DEBUG: Agent unenrolled (detected by timer), switching to enrollment")
            self.disconnected.emit()
            self.close()
            self.timer.stop()


    def _disconnect(self) -> None:
        if hasattr(self.agent, 'loop') and self.agent.loop:
            future = asyncio.run_coroutine_threadsafe(
                self.agent.disconnect(), self.agent.loop
            )
            try:
                future.result(timeout=5)
            except Exception:
                pass
        else:
            asyncio.run(self.agent.disconnect())
        self.disconnected.emit()
        self.close()

class TrayApp(QtWidgets.QSystemTrayIcon):
    disconnected = QtCore.Signal()

    def __init__(self, agent: AgentClient, app: QtWidgets.QApplication) -> None:
        # Some Qt versions don't have SP_ShieldIcon; fall back to a safe icon.
        if hasattr(QtWidgets.QStyle, "SP_ShieldIcon"):
            icon = app.style().standardIcon(QtWidgets.QStyle.SP_ShieldIcon)  # type: ignore
        else:
            icon = app.style().standardIcon(QtWidgets.QStyle.SP_ComputerIcon)  # type: ignore
        super().__init__(icon, app)
        self.agent = agent
        self.setToolTip("SentinelPi-EDR")

        menu = QtWidgets.QMenu()
        status_action = menu.addAction("Open Dashboard")
        status_action.triggered.connect(self._open_dashboard)
        
        disconnect_action = menu.addAction("Disconnect")
        disconnect_action.triggered.connect(self._handle_disconnect)
        
        exit_action = menu.addAction("Exit")
        exit_action.triggered.connect(app.quit)
        self.setContextMenu(menu)

    def _handle_disconnect(self) -> None:
        if hasattr(self.agent, 'loop') and self.agent.loop:
            future = asyncio.run_coroutine_threadsafe(
                self.agent.disconnect(), self.agent.loop
            )
            try:
                future.result(timeout=5)
            except Exception:
                pass
        else:
            asyncio.run(self.agent.disconnect())
        self.disconnected.emit()
        self.showMessage(
            "SentinelPi-EDR",
            "Agent disconnected. Enrollment required.",
            QtWidgets.QSystemTrayIcon.MessageIcon.Information,  # type: ignore
            3000
        )

    def _open_dashboard(self) -> None:
        QtWidgets.QMessageBox.information(None, "SentinelPi-EDR", "Protection active and connected.")  # type: ignore
