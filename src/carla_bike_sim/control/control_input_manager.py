from typing import Dict, Optional
from PySide6.QtCore import QObject, Signal

from .base_controller import BaseController
from .vehicle_control_signal import VehicleControlSignal


class ControlInputManager(QObject):
    """
    控制输入管理器

    负责管理多个控制器实例，处理控制模式切换，并将活动控制器的信号转发给上层。
    确保在任意时刻只有一个控制器处于活动状态。

    Signals:
        control_signal(VehicleControlSignal): 当前活动控制器的控制信号
        active_controller_changed(str): 活动控制器改变时发出，参数为新控制器名称
        controller_error(str, str): 控制器错误信号，参数为(控制器名称, 错误消息)
        controller_status_changed(str, bool, str): 控制器状态改变信号
            - 参数1: 控制器名称
            - 参数2: True表示已连接，False表示已断开
            - 参数3: 状态描述信息
    """

    control_signal = Signal(VehicleControlSignal)
    active_controller_changed = Signal(str)
    controller_error = Signal(str, str)
    controller_status_changed = Signal(str, bool, str)

    def __init__(self):
        super().__init__()
        self._controllers: Dict[str, BaseController] = {}
        self._active_controller_name: Optional[str] = None
        self._active_controller: Optional[BaseController] = None

    def register_controller(self, name: str, controller: BaseController) -> bool:
        if name in self._controllers:
            print(f"警告: 控制器 '{name}' 已存在，将被覆盖")
            if self._active_controller_name == name:
                self._stop_active_controller()

        controller.control_signal_updated.connect(self._on_controller_signal_updated)
        controller.controller_error.connect(
            lambda msg: self._on_controller_error(name, msg)
        )
        controller.controller_status_changed.connect(
            lambda connected, status: self._on_controller_status_changed(
                name, connected, status
            )
        )

        self._controllers[name] = controller
        print(f"控制器 '{name}' 注册成功")
        return True

    def unregister_controller(self, name: str) -> bool:
        if name not in self._controllers:
            print(f"警告: 控制器 '{name}' 不存在")
            return False

        if self._active_controller_name == name:
            self._stop_active_controller()

        controller = self._controllers[name]
        controller.control_signal_updated.disconnect()
        controller.controller_error.disconnect()
        controller.controller_status_changed.disconnect()

        del self._controllers[name]
        print(f"控制器 '{name}' 已注销")
        return True

    def switch_controller(self, name: str) -> bool:
        if name not in self._controllers:
            print(f"错误: 控制器 '{name}' 不存在")
            return False

        if self._active_controller_name == name:
            print(f"控制器 '{name}' 已经是活动状态")
            return True

        if self._active_controller:
            self._stop_active_controller()

        new_controller = self._controllers[name]
        if not new_controller.start():
            print(f"错误: 启动控制器 '{name}' 失败")
            return False

        self._active_controller_name = name
        self._active_controller = new_controller
        self.active_controller_changed.emit(name)
        print(f"已切换到控制器: {name}")
        return True

    def get_active_controller_name(self) -> Optional[str]:
        return self._active_controller_name

    def get_active_controller(self) -> Optional[BaseController]:
        return self._active_controller

    def get_controller(self, name: str) -> Optional[BaseController]:
        return self._controllers.get(name)

    def get_all_controller_names(self) -> list[str]:
        return list(self._controllers.keys())

    def stop_all(self) -> None:
        for name, controller in self._controllers.items():
            if controller.is_running:
                controller.stop()
                print(f"已停止控制器: {name}")

        self._active_controller = None
        self._active_controller_name = None

    def _stop_active_controller(self) -> None:
        if self._active_controller and self._active_controller.is_running:
            self._active_controller.stop()
            print(f"已停止控制器: {self._active_controller_name}")

    def _on_controller_signal_updated(self, control: VehicleControlSignal) -> None:
        sender = self.sender()
        if sender == self._active_controller:
            self.control_signal.emit(control)

    def _on_controller_error(self, name: str, error_msg: str) -> None:
        self.controller_error.emit(name, error_msg)
        print(f"控制器 '{name}' 错误: {error_msg}")

    def _on_controller_status_changed(self, name: str, is_connected: bool, status_msg: str) -> None:
        self.controller_status_changed.emit(name, is_connected, status_msg)
        status = "已连接" if is_connected else "已断开"
        print(f"控制器 '{name}' 状态变化: {status} - {status_msg}")

    def __str__(self) -> str:
        active = self._active_controller_name or "None"
        controllers = ", ".join(self._controllers.keys())
        return (f"ControlInputManager(active={active}, "
                f"registered=[{controllers}])")
