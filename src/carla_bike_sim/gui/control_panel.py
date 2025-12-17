from PySide6.QtWidgets import (
    QWidget,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QGroupBox,
)


class ControlPanel(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        # 连接配置组
        connection_group = self._create_connection_group()
        layout.addWidget(connection_group)

        # 仿真控制组
        simulation_group = self._create_simulation_group()
        layout.addWidget(simulation_group)

        layout.addStretch()
        self.setLayout(layout)

    def _create_connection_group(self):
        """创建连接配置组"""
        group = QGroupBox("CARLA Connection")
        layout = QVBoxLayout()

        # IP 地址输入
        ip_layout = QHBoxLayout()
        ip_layout.addWidget(QLabel("Host:"))
        self.host_input = QLineEdit("localhost")
        self.host_input.setPlaceholderText("e.g., localhost or 192.168.1.100")
        ip_layout.addWidget(self.host_input)
        layout.addLayout(ip_layout)

        # 端口输入
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Port:"))
        self.port_input = QLineEdit("2000")
        self.port_input.setPlaceholderText("e.g., 2000")
        self.port_input.setMaximumWidth(100)
        port_layout.addWidget(self.port_input)
        port_layout.addStretch()
        layout.addLayout(port_layout)

        # 连接/断开按钮
        btn_layout = QHBoxLayout()
        self.connect_btn = QPushButton("🔌 Connect")
        self.disconnect_btn = QPushButton("⏏ Disconnect")
        btn_layout.addWidget(self.connect_btn)
        btn_layout.addWidget(self.disconnect_btn)
        layout.addLayout(btn_layout)

        group.setLayout(layout)
        return group

    def _create_simulation_group(self):
        """创建仿真控制组"""
        group = QGroupBox("Simulation Control")
        layout = QVBoxLayout()

        self.start_btn = QPushButton("▶ Start Simulation")
        self.stop_btn = QPushButton("⏹ Stop Simulation")

        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)

        group.setLayout(layout)
        return group
