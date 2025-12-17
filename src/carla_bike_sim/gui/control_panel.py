from PySide6.QtWidgets import (
    QWidget,
    QPushButton,
    QVBoxLayout,
    QLabel,
)


class ControlPanel(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        layout.addWidget(QLabel("Simulation Control"))

        self.start_btn = QPushButton("▶ Start Simulation")
        self.stop_btn = QPushButton("⏹ Stop Simulation")

        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)
        layout.addStretch()

        self.setLayout(layout)
