from PySide6.QtWidgets import (
    QMainWindow,
    QDockWidget,
    QStatusBar,
    QMessageBox,
)
from PySide6.QtCore import Qt

from carla_bike_sim.gui.central_view import CentralView
from carla_bike_sim.gui.control_panel import ControlPanel
from carla_bike_sim.carla.carla_client_manager import CarlaClientManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CARLA Bicycle Simulator")

        self.carla_manager = None

        self._create_central_view()
        self._create_docks()
        self._create_status_bar()
        self._connect_control_signals()

        # 初始化按钮状态
        self._update_connection_ui(connected=False)

    def _create_central_view(self):
        """中央显示区域（摄像头 / 仿真画面）"""
        self.central_view = CentralView()
        self.setCentralWidget(self.central_view)

    def _create_docks(self):
        """左右 Dock 面板"""

        self.control_panel = ControlPanel()
        control_dock = QDockWidget("Control Panel", self)
        control_dock.setWidget(self.control_panel)
        control_dock.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, control_dock)

        status_dock = QDockWidget("Status", self)
        status_dock.setWidget(self.central_view.create_status_placeholder())
        status_dock.setAllowedAreas(Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, status_dock)

    def _create_status_bar(self):
        status = QStatusBar()
        status.showMessage("Ready")
        self.setStatusBar(status)

    def _connect_carla_signals(self):
        """连接 CARLA 管理器的信号"""
        self.carla_manager.connection_status_changed.connect(self._on_connection_status_changed)
        self.carla_manager.sensor_manager.front_camera_image_ready.connect(self.on_front_camera_image_ready)
        self.carla_manager.sensor_manager.rear_camera_image_ready.connect(self.on_rear_camera_image_ready)
        self.carla_manager.sensor_manager.left_camera_image_ready.connect(self.on_left_camera_image_ready)
        self.carla_manager.sensor_manager.right_camera_image_ready.connect(self.on_right_camera_image_ready)
        self.carla_manager.simulation_error.connect(self._on_simulation_error)

    def _connect_control_signals(self):
        """连接控制面板按钮信号"""
        # 连接控制
        self.control_panel.connect_btn.clicked.connect(self._on_connect)
        self.control_panel.disconnect_btn.clicked.connect(self._on_disconnect)

        # 仿真控制
        self.control_panel.start_btn.clicked.connect(self._on_start_simulation)
        self.control_panel.stop_btn.clicked.connect(self._on_stop_simulation)

    def _on_connect(self):
        """连接按钮点击事件"""
        # 获取用户输入
        host = self.control_panel.host_input.text().strip()
        port_text = self.control_panel.port_input.text().strip()

        # 验证输入
        if not host:
            QMessageBox.warning(self, "Invalid Input", "Host cannot be empty.")
            return

        try:
            port = int(port_text)
            if port < 1 or port > 65535:
                raise ValueError("Port out of range")
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Port must be a number between 1 and 65535.")
            return

        # 创建 CARLA 客户端管理器
        self.statusBar().showMessage(f"Connecting to {host}:{port}...")
        self.carla_manager = CarlaClientManager(host=host, port=port)
        self._connect_carla_signals()

        # 尝试连接
        success = self.carla_manager.connect()

        if not success:
            QMessageBox.warning(
                self,
                "Connection Failed",
                f"Failed to connect to CARLA server at {host}:{port}.\nPlease ensure CARLA is running."
            )
            self.carla_manager = None

    def _on_disconnect(self):
        """断开连接按钮点击事件"""
        if self.carla_manager is not None:
            self.statusBar().showMessage("Disconnecting from CARLA server...")
            self.carla_manager.disconnect()
            self.carla_manager = None
            self._update_connection_ui(connected=False)
            self.central_view.show_placeholder("Disconnected from CARLA server")

    def _on_connection_status_changed(self, connected: bool, message: str):
        """处理连接状态变化"""
        self.statusBar().showMessage(message)
        self._update_connection_ui(connected)

    def _update_connection_ui(self, connected: bool):
        """更新连接相关的 UI 状态"""
        # 连接控制
        self.control_panel.host_input.setEnabled(not connected)
        self.control_panel.port_input.setEnabled(not connected)
        self.control_panel.connect_btn.setEnabled(not connected)
        self.control_panel.disconnect_btn.setEnabled(connected)

        # 仿真控制
        self.control_panel.start_btn.setEnabled(connected)
        self.control_panel.stop_btn.setEnabled(False)

        if not connected:
            self.central_view.show_placeholder("Disconnected from CARLA server")

    def on_front_camera_image_ready(self, image_rgb):
        """处理前摄像头图像更新"""
        self.central_view.update_front_camera_image(image_rgb)

    def on_rear_camera_image_ready(self, image_rgb):
        """处理后摄像头图像更新"""
        self.central_view.update_rear_camera_image(image_rgb)

    def on_left_camera_image_ready(self, image_rgb):
        """处理左摄像头图像更新"""
        self.central_view.update_left_camera_image(image_rgb)

    def on_right_camera_image_ready(self, image_rgb):
        """处理右摄像头图像更新"""
        self.central_view.update_right_camera_image(image_rgb)

    def _on_simulation_error(self, error_message: str):
        """处理仿真错误"""
        self.statusBar().showMessage(f"Error: {error_message}")

    def _on_start_simulation(self):
        if self.carla_manager is None:
            QMessageBox.warning(self, "Not Connected", "Please connect to CARLA server first.")
            return

        self.statusBar().showMessage("Starting simulation...")

        success = self.carla_manager.start_simulation(vehicle_blueprint="vehicle.bh.crossbike")

        if success:
            self.statusBar().showMessage("Simulation started")
            self.control_panel.start_btn.setEnabled(False)
            self.control_panel.stop_btn.setEnabled(True)
        else:
            QMessageBox.warning(
                self,
                "Start Failed",
                "Failed to start simulation. Check the status bar for details."
            )

    def _on_stop_simulation(self):
        """停止仿真按钮点击事件"""
        if self.carla_manager is None:
            return

        self.statusBar().showMessage("Stopping simulation...")
        self.carla_manager.stop_simulation()

        self.statusBar().showMessage("Simulation stopped")
        self.control_panel.start_btn.setEnabled(True)
        self.control_panel.stop_btn.setEnabled(False)
        self.central_view.show_placeholder("Simulation stopped")

    def closeEvent(self, event):
        """窗口关闭事件 - 清理资源"""
        if self.carla_manager is not None:
            self.carla_manager.disconnect()
        event.accept()

