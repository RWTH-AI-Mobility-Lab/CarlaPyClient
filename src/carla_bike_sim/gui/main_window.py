from PySide6.QtWidgets import (
    QMainWindow,
    QDockWidget,
    QStatusBar,
)
from PySide6.QtCore import Qt

from carla_bike_sim.gui.central_view import CentralView
from carla_bike_sim.gui.control_panel import ControlPanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CARLA Bicycle Simulator")

        self._create_central_view()
        self._create_docks()
        self._create_status_bar()

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
