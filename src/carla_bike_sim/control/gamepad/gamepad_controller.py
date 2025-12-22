import pygame
from typing import Optional, Dict
from PySide6.QtCore import QThread, Signal


from ..base_controller import BaseController
from ..vehicle_control_signal import VehicleControlSignal


class GamepadEventThread(QThread):
    """
    事件驱动的游戏手柄线程

    使用 pygame 的事件系统而不是轮询，大幅降低 CPU 占用。
    只在手柄状态实际变化时才处理和发送信号。
    """
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

        self.axis_left_x = config.get('axis_left_x', 0)
        self.axis_left_y = config.get('axis_left_y', 1)
        self.axis_rt = config.get('axis_rt', 5)
        self.axis_lt = config.get('axis_lt', 4)

        self.button_a = config.get('button_a', 0)
        self.button_hand_brake = config.get('button_hand_brake', 0)

        self.current_axies: Dict[int, float] = {}
        self.current_buttons: Dict[int, bool] = {}

    def run(self):
        try:
            if not pygame.get_init():
                pygame.init()
            pygame.joystick.init()

            if not self._connect_joystick():
                return

            self._initialize_state()

            self.running = True
            while self.running:
                try:
                    for event in pygame.event.get():
                        if event.type == pygame.JOYAXISMOTION:
                            print(event.axis, event.value, event.type)
                            self._handle_axis_motion(event)
                        elif event.type == pygame.JOYBUTTONDOWN:
                            self._handle_button_down(event)
                        elif event.type == pygame.JOYBUTTONUP:
                            self._handle_button_up(event)
                        elif event.type == pygame.JOYDEVICEREMOVED:
                            self.error_occurred.emit("手柄已断开连接")
                            self.running = False
                            break

                    if self.running:
                        pygame.time.wait(10)  # 10ms 等待避免完全阻塞

                except Exception as e:
                    self.error_occurred.emit(f"读取手柄数据错误: {str(e)}")

        except Exception as e:
            self.error_occurred.emit(f"手柄线程错误: {str(e)}")

        finally:
            self._cleanup()

    def stop(self):
        self.running = False
        pygame.event.post(pygame.event.Event(pygame.USEREVENT))

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

    def _initialize_state(self):
        if not self.joystick:
            return

        for i in range(self.joystick.get_numaxes()):
            self.current_axies[i] = self.joystick.get_axis(i)

        for i in range(self.joystick.get_numbuttons()):
            self.current_buttons[i] = self.joystick.get_button(i) == 1

        self._emit_current_control()

    def _handle_axis_motion(self, event):
        axis_id = event.axis
        raw_value = event.value

        self.current_axies[axis_id] = raw_value

        if axis_id in [self.axis_left_x, self.axis_rt, self.axis_lt]:
            self._emit_current_control()

    def _handle_button_down(self, event):
        button_id = event.button
        self.current_buttons[button_id] = True

        if button_id == self.button_hand_brake:
            self._emit_current_control()

    def _handle_button_up(self, event):
        button_id = event.button
        self.current_buttons[button_id] = False

        if button_id == self.button_hand_brake:
            self._emit_current_control()

    def _emit_current_control(self):
        throttle = self._get_trigger_value(self.axis_rt)
        brake = self._get_trigger_value(self.axis_lt)
        steer = self._get_axis_value(self.axis_left_x)
        hand_brake = self.current_buttons.get(self.button_hand_brake, False)

        steer *= self.steer_sensitivity

        control = VehicleControlSignal(
            throttle=throttle,
            steer=steer,
            brake=brake,
            hand_brake=hand_brake
        )
        control.clamp()

        self.control_updated.emit(control)

    def _get_axis_value(self, axis_id: int) -> float:
        raw_value = self.current_axies.get(axis_id, 0.0)
        return self._apply_deadzone(raw_value, self.axis_deadzone)

    def _get_trigger_value(self, axis_id: int) -> float:
        raw_value = self.current_axies.get(axis_id, 0.0)
        # 有些手柄扳机是 [-1, 1]，有些是 [0, 1]
        # 统一映射到 [0, 1]
        normalized = (raw_value + 1.0) / 2.0
        return self._apply_deadzone(normalized, self.trigger_deadzone)

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
            except pygame.error as e:
                print("Failed to quit joystick: %s", e)
            except Exception as e:
                print("Unexpected error: %s", e, exc_info=True)
                self.joystick = None


class GamepadController(BaseController):
    """
    游戏手柄控制器 (事件驱动版本)

    使用事件驱动方式处理游戏手柄输入，相比轮询模式大幅降低 CPU 占用。
    支持 Xbox、PlayStation 等标准手柄。

    配置项:
        axis_deadzone (float): 摇杆死区，默认 0.1
        trigger_deadzone (float): 扳机死区，默认 0.05
        steer_sensitivity (float): 转向灵敏度，默认 1.0
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
        self.event_thread: Optional[GamepadEventThread] = None


    def start(self) -> bool:
        if self._is_running:
            print("警告: 游戏手柄控制器已在运行")
            return True

        try:
            self.event_thread = GamepadEventThread(self.config)

            self.event_thread.control_updated.connect(self._on_control_updated)
            self.event_thread.error_occurred.connect(self._on_thread_error)

            self.event_thread.start()

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
            if self.event_thread:
                self.event_thread.stop()
                self.event_thread.wait()

                self.event_thread.control_updated.disconnect()
                self.event_thread.error_occurred.disconnect()

                self.event_thread = None

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

