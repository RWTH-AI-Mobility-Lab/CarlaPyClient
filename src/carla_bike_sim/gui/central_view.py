from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
import numpy as np


class CentralView(QWidget):
    def __init__(self):
        super().__init__()

        self.label = QLabel("Camera View\n(Waiting for connection...)")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet(
            "background-color: #222; color: #ddd; font-size: 20px;"
        )
        self.label.setMinimumSize(800, 600)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.label)
        self.setLayout(layout)

    def update_camera_image(self, image_bgr: np.ndarray):
        """更新摄像头图像

        Args:
            image_rgb: BGR 格式的图像数据 (numpy array)
        """
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
                self.label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )

            self.label.setPixmap(scaled_pixmap)

        except Exception as e:
            print(f"Error updating camera image: {e}")

    def show_placeholder(self, message: str = "Camera View\n(Waiting for connection...)"):
        self.label.clear()
        self.label.setText(message)

    def create_status_placeholder(self):
        label = QLabel("Simulation Status\nROS: OFF\nFPS: --")
        label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        label.setStyleSheet("padding: 8px;")
        return label
