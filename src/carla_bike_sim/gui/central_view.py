from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt


class CentralView(QWidget):
    def __init__(self):
        super().__init__()

        self.label = QLabel("Camera View\n(Placeholder)")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet(
            "background-color: #222; color: #ddd; font-size: 20px;"
        )

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

    def create_status_placeholder(self):
        label = QLabel("Simulation Status\nROS: OFF\nFPS: --")
        label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        label.setStyleSheet("padding: 8px;")
        return label
