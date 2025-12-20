from abc import ABCMeta, abstractmethod
from PySide6.QtCore import QObject, Signal

from .vehicle_control_signal import VehicleControlSignal


class QObjectMeta(type(QObject), ABCMeta):
    pass


class BaseController(QObject, metaclass=QObjectMeta):
    """
    车辆控制器抽象基类

    所有具体控制器（键盘、手柄、蓝牙等）必须继承此类并实现其抽象方法。
    使用 Qt 的信号机制确保线程安全的数据传输。

    Signals:
        control_signal_updated(VehicleControlSignal): 当控制信号更新时发出
        controller_error(str): 当控制器发生错误时发出，参数为错误消息
        controller_status_changed(bool, str): 当控制器状态改变时发出
            - 第一个参数: True表示已连接/启动，False表示断开/停止
            - 第二个参数: 状态描述信息
    """

    control_signal_updated = Signal(VehicleControlSignal)
    controller_error = Signal(str)
    controller_status_changed = Signal(bool, str)

    def __init__(self, config: dict = None):
        super().__init__()
        self.config = config or {}
        self._is_running = False
        self._current_control = VehicleControlSignal()

    @abstractmethod
    def start(self) -> bool:
        """
        启动控制器

        子类必须实现此方法，用于初始化控制器并开始接收输入。

        Returns:
            bool: 启动成功返回 True，失败返回 False
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        """
        停止控制器

        子类必须实现此方法，用于停止接收输入并清理资源。
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """
        获取控制器名称

        子类必须实现此方法，返回控制器的唯一标识名称。

        Returns:
            str: 控制器名称（如 "keyboard", "gamepad", "bluetooth"）
        """
        pass

    @property
    def is_running(self) -> bool:
        """
        获取控制器运行状态

        Returns:
            bool: True表示控制器正在运行，False表示已停止
        """
        return self._is_running

    def get_current_control(self) -> VehicleControlSignal:
        """
        获取当前控制信号

        Returns:
            VehicleControlSignal: 当前的控制信号副本
        """
        return self._current_control.copy()

    def _emit_control_signal(self, control: VehicleControlSignal) -> None:
        """
        发送控制信号（受保护方法）

        子类应调用此方法来发送控制信号更新，会自动进行数值限制。

        Args:
            control (VehicleControlSignal): 要发送的控制信号
        """
        control.clamp()
        self._current_control = control.copy()
        self.control_signal_updated.emit(control)

    def _emit_error(self, error_msg: str) -> None:
        """
        发送错误信号（受保护方法）

        子类应调用此方法来报告错误。

        Args:
            error_msg (str): 错误消息
        """
        self.controller_error.emit(error_msg)

    def _emit_status_change(self, is_connected: bool, status_msg: str) -> None:
        """
        发送状态变化信号（受保护方法）

        子类应调用此方法来报告状态变化。

        Args:
            is_connected (bool): True表示已连接，False表示已断开
            status_msg (str): 状态描述信息
        """
        self.controller_status_changed.emit(is_connected, status_msg)

    def __str__(self) -> str:
        """
        返回控制器的字符串表示

        Returns:
            str: 控制器描述
        """
        return f"{self.get_name()} Controller (running={self._is_running})"
