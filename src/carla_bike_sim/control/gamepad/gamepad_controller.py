import time
import pygame
from typing import Optional
from PySide6.QtCore import QThread, Signal


from ..base_controller import BaseController
from ..vehicle_control_signal import VehicleControlSignal


class GamepadPollingThread(QThread):
    control_updated = Signal(VehicleControlSignal)
    error_occurred = Signal(str)

    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.joystick: Optional[pygame.joystick.Joystick] = None
        self.running = False

        self.axis_deadzone = config.get('axis_deadzone', 0.1)
        self.trigger_deadzone = config.get('trigger_deadzone', 0.05)
        self.steer_sensitivity = config.get('steer_sensitivity', 1.0)
        self.poll_interval = config.get('poll_interval', 20) / 1000.0

        self.axis_left_x = config.get('axis_left_x', 0)
        self.axis_left_y = config.get('axis_left_y', 1)
        self.axis_rt = config.get('axis_rt', 5)
        self.axis_lt = config.get('axis_lt', 4)

        self.button_a = config.get('button_a', 0)
        self.button_hand_brake = config.get('button_hand_brake', 0)

    def run(self):
        try:
            if not pygame.get_init():
                pygame.init()
            pygame.joystick.init()

            if not self._connect_joystick():
                return

            self.running = True
            while self.running:
                try:
                    pygame.event.pump()
                    control_signal = self._read_control_signal()
                    self.control_updated.emit(control_signal)
                    time.sleep(self.poll_interval)

                except Exception as e:
                    self.error_occurred.emit(f"读取手柄数据错误: {str(e)}")
                    # time.sleep(0.1)

        except Exception as e:
            self.error_occurred.emit(f"手柄线程错误: {str(e)}")

        finally:
            self._cleanup()

    def stop(self):
        self.running = False

    def _connect_joystick(self) -> bool:
        joystick_count = pygame.joystick.get_count()

        if joystick_count == 0:
            self.error_occurred.emit("未检测到游戏手柄，请连接手柄后重试")
            return False

        try:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()

            joystick_name = self.joystick.get_name()
            print(f"✅ 手柄已连接: {joystick_name}")
            print(f"   轴数量: {self.joystick.get_numaxes()}")
            print(f"   按钮数量: {self.joystick.get_numbuttons()}")

            return True

        except Exception as e:
            self.error_occurred.emit(f"连接手柄失败: {str(e)}")
            return False

    def _read_control_signal(self) -> VehicleControlSignal:
        if not self.joystick:
            return VehicleControlSignal()

        throttle = self._get_trigger_value(self.axis_rt)
        brake = self._get_trigger_value(self.axis_lt)
        steer = self._get_axis_value(self.axis_left_x)
        hand_brake = self._get_button_state(self.button_hand_brake)

        steer *= self.steer_sensitivity

        control = VehicleControlSignal(
            throttle=throttle,
            steer=steer,
            brake=brake,
            hand_brake=hand_brake
        )
        control.clamp()

        return control

    def _get_axis_value(self, axis_id: int) -> float:
        if not self.joystick or axis_id >= self.joystick.get_numaxes():
            return 0.0

        raw_value = self.joystick.get_axis(axis_id)
        return self._apply_deadzone(raw_value, self.axis_deadzone)

    def _get_trigger_value(self, axis_id: int) -> float:
        if not self.joystick or axis_id >= self.joystick.get_numaxes():
            return 0.0

        raw_value = self.joystick.get_axis(axis_id)
        # 有些手柄扳机是 [-1, 1]，有些是 [0, 1]
        # 统一映射到 [0, 1]
        normalized = (raw_value + 1.0) / 2.0
        return self._apply_deadzone(normalized, self.trigger_deadzone)

    def _get_button_state(self, button_id: int) -> bool:
        if not self.joystick or button_id >= self.joystick.get_numbuttons():
            return False

        return self.joystick.get_button(button_id) == 1

    def _apply_deadzone(self, value: float, deadzone: float) -> float:
        if abs(value) < deadzone:
            return 0.0
        if value > 0:
            return (value - deadzone) / (1.0 - deadzone)
        else:
            return (value + deadzone) / (1.0 - deadzone)

    def _cleanup(self):
        if self.joystick:
            try:
                self.joystick.quit()
            except:
                pass
            self.joystick = None


class GamepadController(BaseController):
    """
    游戏手柄控制器

    使用独立线程轮询游戏手柄输入，支持 Xbox、PlayStation 等标准手柄。

    配置项:
        axis_deadzone (float): 摇杆死区，默认 0.1
        trigger_deadzone (float): 扳机死区，默认 0.05
        steer_sensitivity (float): 转向灵敏度，默认 1.0
        poll_interval (int): 轮询间隔（毫秒），默认 20ms
        axis_left_x (int): 左摇杆 X 轴编号，默认 0
        axis_left_y (int): 左摇杆 Y 轴编号，默认 1
        axis_rt (int): 右扳机轴编号，默认 5
        axis_lt (int): 左扳机轴编号，默认 4
        button_a (int): A 按钮编号，默认 0
        button_hand_brake (int): 手刹按钮编号，默认 0

    控制映射:
        右扳机 (RT) -> 油门
        左扳机 (LT) -> 刹车
        左摇杆 X 轴 -> 转向
        A 按钮 -> 手刹
    """

    def __init__(self, config: dict = None):
        super().__init__(config)
        self.polling_thread: Optional[GamepadPollingThread] = None


    def start(self) -> bool:
        if self._is_running:
            print("警告: 游戏手柄控制器已在运行")
            return True

        try:
            self.polling_thread = GamepadPollingThread(self.config)

            self.polling_thread.control_updated.connect(self._on_control_updated)
            self.polling_thread.error_occurred.connect(self._on_thread_error)

            self.polling_thread.start()

            self._is_running = True
            self._emit_status_change(True, "游戏手柄控制器已启动")
            print("✅ 游戏手柄控制器已启动")
            return True

        except Exception as e:
            error_msg = f"启动游戏手柄控制器失败: {str(e)}"
            self._emit_error(error_msg)
            print(f"❌ {error_msg}")
            return False

    def stop(self) -> None:
        if not self._is_running:
            return

        try:
            if self.polling_thread:
                self.polling_thread.stop()
                self.polling_thread.wait()

                self.polling_thread.control_updated.disconnect()
                self.polling_thread.error_occurred.disconnect()

                self.polling_thread = None

            self._is_running = False

            self._current_control.reset()
            self._emit_control_signal(self._current_control)

            self._emit_status_change(False, "游戏手柄控制器已停止")
            print("⏹️  游戏手柄控制器已停止")

        except Exception as e:
            print(f"停止游戏手柄控制器时出错: {str(e)}")

    def get_name(self) -> str:
        return "gamepad"

    def _on_control_updated(self, control: VehicleControlSignal):
        self._emit_control_signal(control)

    def _on_thread_error(self, error_msg: str):
        self._emit_error(error_msg)

