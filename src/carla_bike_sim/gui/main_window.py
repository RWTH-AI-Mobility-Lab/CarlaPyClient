from PySide6.QtWidgets import (
    QMainWindow,
    QDockWidget,
    QStatusBar,
    QMessageBox,
)
from PySide6.QtCore import Qt, QTimer

from carla_bike_sim.gui.central_view import CentralView
from carla_bike_sim.gui.control_panel import ControlPanel
from carla_bike_sim.carla.carla_client_manager import CarlaClientManager
from carla_bike_sim.gui.status_panel import StatusPanel
from carla_bike_sim.control import ControlInputManager, VehicleControlSignal
from carla_bike_sim.control.gamepad import GamepadController


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CARLA Bicycle Simulator")

        self.carla_manager = None
        self.control_panel = None
        self.central_view = None
        self.status_panel = None
        self.control_input_manager = None

        self._create_central_view()
        self._create_docks()
        self._create_status_bar()
        self._setup_control_input()
        self._connect_control_signals()

        self.vehicle_update_timer = QTimer()
        self.vehicle_update_timer.timeout.connect(self._update_vehicle_status)
        self.vehicle_update_timer.setInterval(50)

        self._update_connection_ui(connected=False)

    def _create_central_view(self):
        self.central_view = CentralView()
        self.setCentralWidget(self.central_view)

    def _create_docks(self):
        self.control_panel = ControlPanel()
        control_dock = QDockWidget("Control Panel", self)
        control_dock.setWidget(self.control_panel)
        control_dock.setAllowedAreas(Qt.LeftDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, control_dock)

        self.status_panel = StatusPanel()
        status_dock = QDockWidget("Status", self)
        status_dock.setWidget(self.status_panel)
        status_dock.setAllowedAreas(Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, status_dock)

    def _create_status_bar(self):
        status = QStatusBar()
        status.showMessage("Ready")
        self.setStatusBar(status)

    def _setup_control_input(self):
        self.control_input_manager = ControlInputManager()

        gamepad_config = {
            'axis_deadzone': 0.1,
            'trigger_deadzone': 0.05,
            'steer_sensitivity': 1.0,
            'poll_interval': 20,
        }
        gamepad_ctrl = GamepadController(gamepad_config)
        self.control_input_manager.register_controller("gamepad", gamepad_ctrl)

        self.control_input_manager.control_signal.connect(
            self._on_vehicle_control_signal,
            Qt.ConnectionType.QueuedConnection
        )

    def _connect_carla_signals(self):
        """连接 CARLA 管理器的信号"""
        # 使用 QueuedConnection 确保跨线程安全
        # CARLA 的回调在后台线程执行，必须使用队列连接
        self.carla_manager.connection_status_changed.connect(
            self._on_connection_status_changed,
            Qt.ConnectionType.QueuedConnection
        )
        self.carla_manager.sensor_manager.front_camera_image_ready.connect(
            self.on_front_camera_image_ready,
            Qt.ConnectionType.QueuedConnection
        )
        self.carla_manager.sensor_manager.rear_camera_image_ready.connect(
            self.on_rear_camera_image_ready,
            Qt.ConnectionType.QueuedConnection
        )
        self.carla_manager.sensor_manager.left_camera_image_ready.connect(
            self.on_left_camera_image_ready,
            Qt.ConnectionType.QueuedConnection
        )
        self.carla_manager.sensor_manager.right_camera_image_ready.connect(
            self.on_right_camera_image_ready,
            Qt.ConnectionType.QueuedConnection
        )
        self.carla_manager.simulation_error.connect(
            self._on_simulation_error,
            Qt.ConnectionType.QueuedConnection
        )

    def _connect_control_signals(self):
        self.control_panel.connect_btn.clicked.connect(self._on_connect)
        self.control_panel.disconnect_btn.clicked.connect(self._on_disconnect)

        self.control_panel.start_btn.clicked.connect(self._on_start_simulation)
        self.control_panel.stop_btn.clicked.connect(self._on_stop_simulation)

    def _on_connect(self):
        host = self.control_panel.host_input.text().strip()
        port_text = self.control_panel.port_input.text().strip()

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

        self.statusBar().showMessage(f"Connecting to {host}:{port}...")
        self.carla_manager = CarlaClientManager(host=host, port=port)
        self._connect_carla_signals()

        success = self.carla_manager.connect()

        if not success:
            QMessageBox.warning(
                self,
                "Connection Failed",
                f"Failed to connect to CARLA server at {host}:{port}.\nPlease ensure CARLA is running."
            )
            self.carla_manager = None
        
        self.central_view.show_placeholder("Waiting for simulation start")

    def _on_disconnect(self):
        if self.carla_manager is not None:
            self.statusBar().showMessage("Disconnecting from CARLA server...")
            self.carla_manager.disconnect()
            self.carla_manager = None
            self.status_panel.reset()
            self._update_connection_ui(connected=False)
            self.central_view.show_placeholder("Disconnected from CARLA server")

    def _on_connection_status_changed(self, connected: bool, message: str):
        self.statusBar().showMessage(message)
        self._update_connection_ui(connected)

    def _update_connection_ui(self, connected: bool):
        self.control_panel.host_input.setEnabled(not connected)
        self.control_panel.port_input.setEnabled(not connected)
        self.control_panel.connect_btn.setEnabled(not connected)
        self.control_panel.disconnect_btn.setEnabled(connected)

        self.control_panel.start_btn.setEnabled(connected)
        self.control_panel.stop_btn.setEnabled(False)

        if not connected:
            self.central_view.show_placeholder("Disconnected from CARLA server")

    def on_front_camera_image_ready(self, image_rgb):
        self.central_view.update_front_camera_image(image_rgb)
        self.status_panel.on_camera_frame_received('front')

    def on_rear_camera_image_ready(self, image_rgb):
        self.central_view.update_rear_camera_image(image_rgb)
        self.status_panel.on_camera_frame_received('rear')

    def on_left_camera_image_ready(self, image_rgb):
        self.central_view.update_left_camera_image(image_rgb)
        self.status_panel.on_camera_frame_received('left')

    def on_right_camera_image_ready(self, image_rgb):
        self.central_view.update_right_camera_image(image_rgb)
        self.status_panel.on_camera_frame_received('right')

    def _on_simulation_error(self, error_message: str):
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
            self.vehicle_update_timer.start()
            self.control_input_manager.switch_controller("gamepad")
        else:
            QMessageBox.warning(
                self,
                "Start Failed",
                "Failed to start simulation. Check the status bar for details."
            )

    def _on_stop_simulation(self):
        if self.carla_manager is None:
            return

        self.statusBar().showMessage("Stopping simulation...")

        self.vehicle_update_timer.stop()
        self.control_input_manager.stop_all()
        self.carla_manager.stop_simulation()

        self.statusBar().showMessage("Simulation stopped")
        self.control_panel.start_btn.setEnabled(True)
        self.control_panel.stop_btn.setEnabled(False)
        self.central_view.show_placeholder("Simulation stopped")

        self.status_panel.reset()

    def _update_vehicle_status(self):
        if self.carla_manager is None or not self.carla_manager.is_running:
            return

        velocity = self.carla_manager.get_vehicle_velocity()
        if velocity is not None:
            import math
            speed = math.sqrt(velocity.x**2 + velocity.y**2 + velocity.z**2)
            self.status_panel.update_vehicle_velocity(speed)

        transform = self.carla_manager.get_vehicle_transform()
        if transform is not None:
            loc = transform.location
            rot = transform.rotation
            self.status_panel.update_vehicle_transform(
                loc.x, loc.y, loc.z,
                rot.pitch, rot.yaw, rot.roll
            )

        if self.carla_manager.vehicle is not None:
            control = self.carla_manager.vehicle.get_control()
            self.status_panel.update_vehicle_control(
                control.throttle,
                control.brake,
                control.steer
            )
            self.status_panel.update_vehicle_gear(control.gear)

    def _on_vehicle_control_signal(self, control: VehicleControlSignal):
        if self.carla_manager and self.carla_manager.is_running:
            self.carla_manager.set_vehicle_control(
                throttle=control.throttle,
                steer=control.steer,
                brake=control.brake,
                hand_brake=control.hand_brake
            )

    def closeEvent(self, event):
        self.vehicle_update_timer.stop()
        if self.control_input_manager:
            self.control_input_manager.stop_all()
        if self.carla_manager is not None:
            self.carla_manager.disconnect()
        event.accept()

