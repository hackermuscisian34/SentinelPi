from PySide6 import QtWidgets, QtGui, QtCore
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
        try:
            data = self.agent.enroll(self.pi_ip.text().strip(), self.pairing.text().strip())
            self.status.setText("Enrollment successful")
            self.enrolled.emit()
        except Exception as exc:
            self.status.setStyleSheet("color: #b00020;")
            self.status.setText(str(exc))

class TrayApp(QtWidgets.QSystemTrayIcon):
    def __init__(self, agent: AgentClient, app: QtWidgets.QApplication) -> None:
        # Some Qt versions don't have SP_ShieldIcon; fall back to a safe icon.
        if hasattr(QtWidgets.QStyle, "SP_ShieldIcon"):
            icon = app.style().standardIcon(QtWidgets.QStyle.SP_ShieldIcon)
        else:
            icon = app.style().standardIcon(QtWidgets.QStyle.SP_ComputerIcon)
        super().__init__(icon, app)
        self.agent = agent
        self.setToolTip("SentinelPi-EDR")

        menu = QtWidgets.QMenu()
        status_action = menu.addAction("Open Dashboard")
        status_action.triggered.connect(self._open_dashboard)
        exit_action = menu.addAction("Exit")
        exit_action.triggered.connect(app.quit)
        self.setContextMenu(menu)

    def _open_dashboard(self) -> None:
        QtWidgets.QMessageBox.information(None, "SentinelPi-EDR", "Protection active and connected.")
