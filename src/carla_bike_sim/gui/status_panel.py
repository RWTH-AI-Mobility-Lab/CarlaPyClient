from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QGroupBox,
    QGridLayout,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
import time


class StatusPanel(QWidget):
    """状态面板，显示实时的车辆和传感器信息"""

    def __init__(self):
        super().__init__()
        self.setMinimumWidth(250)

        self._camera_frame_times = {
            'front': [],
            'rear': [],
            'left': [],
            'right': []
        }
        self._fps_window_size = 30

        self._setup_ui()

        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._update_display)
        self._update_timer.start(50)

        self._cached_data = {
            'velocity': 0.0,
            'throttle': 0.0,
            'brake': 0.0,
            'steer': 0.0,
            'gear': 0,
            'position_x': 0.0,
            'position_y': 0.0,
            'position_z': 0.0,
            'rotation_pitch': 0.0,
            'rotation_yaw': 0.0,
            'rotation_roll': 0.0,
        }

    def _setup_ui(self):
        """创建UI组件"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)

        # FPS
        camera_group = self._create_camera_fps_group()
        main_layout.addWidget(camera_group)

        # 车辆状态
        vehicle_group = self._create_vehicle_status_group()
        main_layout.addWidget(vehicle_group)

        # 控制输入
        control_group = self._create_control_group()
        main_layout.addWidget(control_group)

        transform_group = self._create_transform_group()
        main_layout.addWidget(transform_group)

        main_layout.addStretch()
        self.setLayout(main_layout)

    def _create_camera_fps_group(self):
        group = QGroupBox("Camera FPS")
        layout = QGridLayout()
        layout.setSpacing(5)

        self.front_fps_label = self._create_value_label("-- fps")
        self.rear_fps_label = self._create_value_label("-- fps")
        self.left_fps_label = self._create_value_label("-- fps")
        self.right_fps_label = self._create_value_label("-- fps")

        layout.addWidget(QLabel("Front:"), 0, 0)
        layout.addWidget(self.front_fps_label, 0, 1)
        layout.addWidget(QLabel("Rear:"), 1, 0)
        layout.addWidget(self.rear_fps_label, 1, 1)
        layout.addWidget(QLabel("Left:"), 2, 0)
        layout.addWidget(self.left_fps_label, 2, 1)
        layout.addWidget(QLabel("Right:"), 3, 0)
        layout.addWidget(self.right_fps_label, 3, 1)

        group.setLayout(layout)
        return group

    def _create_vehicle_status_group(self):
        group = QGroupBox("Vehicle Status")
        layout = QGridLayout()
        layout.setSpacing(5)

        velocity_label = QLabel("Speed:")
        self.velocity_value = QLabel("0.0 km/h")
        # self.velocity_value.setFont(QFont("Arial", 14, QFont.Bold))
        # self.velocity_value.setStyleSheet("color: #2196F3;")

        self.gear_label = self._create_value_label("N")

        layout.addWidget(velocity_label, 0, 0)
        layout.addWidget(self.velocity_value, 0, 1, 1, 2)
        layout.addWidget(QLabel("Gear:"), 1, 0)
        layout.addWidget(self.gear_label, 1, 1)

        group.setLayout(layout)
        return group

    def _create_control_group(self):
        group = QGroupBox("Control Inputs")
        layout = QGridLayout()
        layout.setSpacing(5)

        self.throttle_label = self._create_value_label("0.0%")
        self.brake_label = self._create_value_label("0.0%")
        self.steer_label = self._create_value_label("0.0")

        layout.addWidget(QLabel("Throttle:"), 0, 0)
        layout.addWidget(self.throttle_label, 0, 1)
        layout.addWidget(QLabel("Brake:"), 1, 0)
        layout.addWidget(self.brake_label, 1, 1)
        layout.addWidget(QLabel("Steering:"), 2, 0)
        layout.addWidget(self.steer_label, 2, 1)

        group.setLayout(layout)
        return group

    def _create_transform_group(self):
        group = QGroupBox("Transform")
        layout = QVBoxLayout()
        layout.setSpacing(3)

        position_layout = QGridLayout()
        position_layout.setSpacing(5)
        self.pos_x_label = self._create_value_label("0.0")
        self.pos_y_label = self._create_value_label("0.0")
        self.pos_z_label = self._create_value_label("0.0")

        position_layout.addWidget(QLabel("X:"), 0, 0)
        position_layout.addWidget(self.pos_x_label, 0, 1)
        position_layout.addWidget(QLabel("Y:"), 1, 0)
        position_layout.addWidget(self.pos_y_label, 1, 1)
        position_layout.addWidget(QLabel("Z:"), 2, 0)
        position_layout.addWidget(self.pos_z_label, 2, 1)

        rotation_layout = QGridLayout()
        rotation_layout.setSpacing(5)
        self.rot_pitch_label = self._create_value_label("0.0°")
        self.rot_yaw_label = self._create_value_label("0.0°")
        self.rot_roll_label = self._create_value_label("0.0°")

        rotation_layout.addWidget(QLabel("Pitch:"), 0, 0)
        rotation_layout.addWidget(self.rot_pitch_label, 0, 1)
        rotation_layout.addWidget(QLabel("Yaw:"), 1, 0)
        rotation_layout.addWidget(self.rot_yaw_label, 1, 1)
        rotation_layout.addWidget(QLabel("Roll:"), 2, 0)
        rotation_layout.addWidget(self.rot_roll_label, 2, 1)

        layout.addWidget(QLabel("Position (m):"))
        layout.addLayout(position_layout)
        layout.addWidget(QLabel("Rotation:"))
        layout.addLayout(rotation_layout)

        group.setLayout(layout)
        return group

    def _create_value_label(self, text: str = "") -> QLabel:
        label = QLabel(text)
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        label.setStyleSheet("QLabel { font-family: 'Consolas', 'Courier New', monospace; }")
        return label

    def _update_display(self):
        self._update_camera_fps_display()
        self._update_vehicle_display()

    def _update_camera_fps_display(self):
        front_fps = self._calculate_fps('front')
        rear_fps = self._calculate_fps('rear')
        left_fps = self._calculate_fps('left')
        right_fps = self._calculate_fps('right')

        self.front_fps_label.setText(f"{front_fps:.1f} fps" if front_fps > 0 else "-- fps")
        self.rear_fps_label.setText(f"{rear_fps:.1f} fps" if rear_fps > 0 else "-- fps")
        self.left_fps_label.setText(f"{left_fps:.1f} fps" if left_fps > 0 else "-- fps")
        self.right_fps_label.setText(f"{right_fps:.1f} fps" if right_fps > 0 else "-- fps")

    def _update_vehicle_display(self):
        data = self._cached_data

        velocity_kmh = data['velocity'] * 3.6
        self.velocity_value.setText(f"{velocity_kmh:.1f} km/h")

        self.throttle_label.setText(f"{data['throttle'] * 100:.1f}%")
        self.brake_label.setText(f"{data['brake'] * 100:.1f}%")
        self.steer_label.setText(f"{data['steer']:.2f}")

        gear = data['gear']
        if gear == 0:
            gear_str = "N"
        elif gear > 0:
            gear_str = f"D{gear}"
        else:
            gear_str = "R"
        self.gear_label.setText(gear_str)

        self.pos_x_label.setText(f"{data['position_x']:.2f}")
        self.pos_y_label.setText(f"{data['position_y']:.2f}")
        self.pos_z_label.setText(f"{data['position_z']:.2f}")

        self.rot_pitch_label.setText(f"{data['rotation_pitch']:.1f}°")
        self.rot_yaw_label.setText(f"{data['rotation_yaw']:.1f}°")
        self.rot_roll_label.setText(f"{data['rotation_roll']:.1f}°")

    def on_camera_frame_received(self, camera_name: str):
        if camera_name not in self._camera_frame_times:
            return

        current_time = time.time()
        times = self._camera_frame_times[camera_name]
        times.append(current_time)

        if len(times) > self._fps_window_size:
            times.pop(0)

    def _calculate_fps(self, camera_name: str) -> float:
        times = self._camera_frame_times.get(camera_name, [])

        if len(times) < 2:
            return 0.0

        time_span = times[-1] - times[0]

        if time_span > 0:
            fps = (len(times) - 1) / time_span
            return fps

        return 0.0

    def update_vehicle_velocity(self, velocity: float):
        self._cached_data['velocity'] = velocity

    def update_vehicle_control(self, throttle: float, brake: float, steer: float):
        self._cached_data['throttle'] = throttle
        self._cached_data['brake'] = brake
        self._cached_data['steer'] = steer

    def update_vehicle_gear(self, gear: int):
        self._cached_data['gear'] = gear

    def update_vehicle_transform(self, location_x: float, location_y: float, location_z: float,
                                 rotation_pitch: float, rotation_yaw: float, rotation_roll: float):
        self._cached_data['position_x'] = location_x
        self._cached_data['position_y'] = location_y
        self._cached_data['position_z'] = location_z
        self._cached_data['rotation_pitch'] = rotation_pitch
        self._cached_data['rotation_yaw'] = rotation_yaw
        self._cached_data['rotation_roll'] = rotation_roll

    def reset(self):
        for camera_name in self._camera_frame_times:
            self._camera_frame_times[camera_name].clear()

        self._cached_data = {
            'velocity': 0.0,
            'throttle': 0.0,
            'brake': 0.0,
            'steer': 0.0,
            'gear': 0,
            'position_x': 0.0,
            'position_y': 0.0,
            'position_z': 0.0,
            'rotation_pitch': 0.0,
            'rotation_yaw': 0.0,
            'rotation_roll': 0.0,
        }

        self.front_fps_label.setText("-- fps")
        self.rear_fps_label.setText("-- fps")
        self.left_fps_label.setText("-- fps")
        self.right_fps_label.setText("-- fps")
