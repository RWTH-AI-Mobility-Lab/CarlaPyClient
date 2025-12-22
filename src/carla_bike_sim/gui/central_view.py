from PySide6.QtWidgets import QWidget, QLabel, QGridLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
import numpy as np


class CentralView(QWidget):
    def __init__(self):
        super().__init__()

        self.front_label = self._create_camera_label("前摄像头\n(Waiting for connection...)")
        self.rear_label = self._create_camera_label("后摄像头\n(Waiting for connection...)")
        self.left_label = self._create_camera_label("左摄像头\n(Waiting for connection...)")
        self.right_label = self._create_camera_label("右摄像头\n(Waiting for connection...)")

        layout = QGridLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        # front, rear, left, right
        layout.addWidget(self.front_label, 0, 0)
        layout.addWidget(self.rear_label, 0, 1)
        layout.addWidget(self.left_label, 1, 0)
        layout.addWidget(self.right_label, 1, 1)

        self.setLayout(layout)

    def _create_camera_label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet(
            "background-color: #222; color: #ddd; font-size: 16px; border: 1px solid #444;"
        )
        label.setMinimumSize(400, 300)
        label.setScaledContents(False)
        return label

    def _update_camera_image(self, label: QLabel, image_bgr: np.ndarray):
        try:
            if not image_bgr.flags['C_CONTIGUOUS']:
                image_bgr = np.ascontiguousarray(image_bgr)

            height, width, channel = image_bgr.shape
            bytes_per_line = channel * width

            # 将 numpy 数组转换为 QImage (BGR888 格式)
            q_image = QImage(
                image_bgr.data,
                width,
                height,
                bytes_per_line,
                QImage.Format_BGR888
            )

            q_image = q_image.copy()

            pixmap = QPixmap.fromImage(q_image)
            scaled_pixmap = pixmap.scaled(
                label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            label.setPixmap(scaled_pixmap)

        except Exception as e:
            print(f"Error updating camera image: {e}")

    def update_front_camera_image(self, image_bgr: np.ndarray):
        self._update_camera_image(self.front_label, image_bgr)

    def update_rear_camera_image(self, image_bgr: np.ndarray):
        self._update_camera_image(self.rear_label, image_bgr)

    def update_left_camera_image(self, image_bgr: np.ndarray):
        self._update_camera_image(self.left_label, image_bgr)

    def update_right_camera_image(self, image_bgr: np.ndarray):
        self._update_camera_image(self.right_label, image_bgr)

    def show_placeholder(self, message: str = "Camera View\n(Waiting for connection...)"):
        self.front_label.clear()
        self.front_label.setText(f"前摄像头\n{message}")
        self.rear_label.clear()
        self.rear_label.setText(f"后摄像头\n{message}")
        self.left_label.clear()
        self.left_label.setText(f"左摄像头\n{message}")
        self.right_label.clear()
        self.right_label.setText(f"右摄像头\n{message}")
