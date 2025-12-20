"""
游戏手柄测试脚本

测试手柄输入读取，实时显示手柄的按键、摇杆和扳机状态，
并输出映射后的车辆控制信号（油门、转向、刹车）。

使用方法:
    python test/gamepad_test.py

按 ESC 或 Ctrl+C 退出程序
"""
import sys
import os
import time

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import pygame
except ImportError:
    print("错误: 需要安装 pygame 库")
    print("请运行: pip install pygame")
    sys.exit(1)


class GamepadTester:
    """游戏手柄测试器"""

    def __init__(self):
        """初始化 pygame 和手柄"""
        pygame.init()
        pygame.joystick.init()

        # 手柄配置
        self.joystick = None
        self.running = True

        # 死区配置
        self.axis_deadzone = 0.1      # 摇杆死区
        self.trigger_deadzone = 0.05  # 扳机死区

        # Xbox 手柄轴映射 (标准布局)
        self.AXIS_LEFT_X = 0      # 左摇杆 X 轴
        self.AXIS_LEFT_Y = 1      # 左摇杆 Y 轴
        self.AXIS_RIGHT_X = 2     # 右摇杆 X 轴 (某些手柄是 3)
        self.AXIS_RIGHT_Y = 3     # 右摇杆 Y 轴 (某些手柄是 4)
        self.AXIS_LT = 4          # 左扳机 (某些手柄是 2)
        self.AXIS_RT = 5          # 右扳机 (某些手柄是 5)

        # Xbox 手柄按键映射
        self.BUTTON_A = 0
        self.BUTTON_B = 1
        self.BUTTON_X = 2
        self.BUTTON_Y = 3
        self.BUTTON_LB = 4
        self.BUTTON_RB = 5
        self.BUTTON_BACK = 6
        self.BUTTON_START = 7
        self.BUTTON_LS = 8   # 左摇杆按下
        self.BUTTON_RS = 9   # 右摇杆按下

    def connect_gamepad(self) -> bool:
        """
        连接第一个检测到的游戏手柄

        Returns:
            bool: 连接成功返回 True
        """
        joystick_count = pygame.joystick.get_count()

        if joystick_count == 0:
            print("❌ 未检测到游戏手柄，请连接手柄后重试")
            return False

        # 连接第一个手柄
        self.joystick = pygame.joystick.Joystick(0)
        self.joystick.init()

        print("\n" + "="*60)
        print("✅ 手柄连接成功!")
        print("="*60)
        print(f"手柄名称: {self.joystick.get_name()}")
        print(f"轴数量: {self.joystick.get_numaxes()}")
        print(f"按钮数量: {self.joystick.get_numbuttons()}")
        print(f"方向键数量: {self.joystick.get_numhats()}")
        print("="*60 + "\n")

        return True

    def apply_deadzone(self, value: float, deadzone: float) -> float:
        """
        应用死区处理

        Args:
            value: 原始输入值
            deadzone: 死区阈值

        Returns:
            float: 处理后的值
        """
        if abs(value) < deadzone:
            return 0.0
        # 重新映射到 [0, 1] 或 [-1, 1]
        if value > 0:
            return (value - deadzone) / (1.0 - deadzone)
        else:
            return (value + deadzone) / (1.0 - deadzone)

    def get_axis_value(self, axis_id: int) -> float:
        """
        获取轴的值（带死区处理）

        Args:
            axis_id: 轴 ID

        Returns:
            float: 轴的值，范围 [-1.0, 1.0]
        """
        if not self.joystick or axis_id >= self.joystick.get_numaxes():
            return 0.0

        raw_value = self.joystick.get_axis(axis_id)
        return self.apply_deadzone(raw_value, self.axis_deadzone)

    def get_trigger_value(self, axis_id: int) -> float:
        """
        获取扳机值（带死区处理）

        扳机通常范围是 [-1, 1]，需要映射到 [0, 1]

        Args:
            axis_id: 扳机轴 ID

        Returns:
            float: 扳机值，范围 [0.0, 1.0]
        """
        if not self.joystick or axis_id >= self.joystick.get_numaxes():
            return 0.0

        raw_value = self.joystick.get_axis(axis_id)
        # 有些手柄扳机是 [-1, 1]，有些是 [0, 1]
        # 统一映射到 [0, 1]
        normalized = (raw_value + 1.0) / 2.0
        return self.apply_deadzone(normalized, self.trigger_deadzone)

    def get_button_state(self, button_id: int) -> bool:
        """
        获取按钮状态

        Args:
            button_id: 按钮 ID

        Returns:
            bool: 按钮是否按下
        """
        if not self.joystick or button_id >= self.joystick.get_numbuttons():
            return False

        return self.joystick.get_button(button_id) == 1

    def get_vehicle_control_signal(self) -> dict:
        """
        获取车辆控制信号

        映射规则:
            - 右扳机 (RT) -> 油门
            - 左扳机 (LT) -> 刹车
            - 左摇杆 X 轴 -> 转向
            - A 按钮 -> 手刹

        Returns:
            dict: 包含 throttle, steer, brake, hand_brake 的字典
        """
        # 读取原始输入
        throttle = self.get_trigger_value(self.AXIS_RT)  # 右扳机
        brake = self.get_trigger_value(self.AXIS_LT)     # 左扳机
        steer = self.get_axis_value(self.AXIS_LEFT_X)    # 左摇杆 X
        hand_brake = self.get_button_state(self.BUTTON_A)  # A 按钮

        # 限制范围
        throttle = max(0.0, min(1.0, throttle))
        brake = max(0.0, min(1.0, brake))
        steer = max(-1.0, min(1.0, steer))

        return {
            'throttle': throttle,
            'steer': steer,
            'brake': brake,
            'hand_brake': hand_brake
        }

    def print_status(self, control_signal: dict):
        """
        打印当前状态（清屏后打印）

        Args:
            control_signal: 车辆控制信号字典
        """
        # 清屏 (Windows: cls, Linux/Mac: clear)
        os.system('cls' if os.name == 'nt' else 'clear')

        print("╔" + "═"*58 + "╗")
        print("║" + " "*15 + "游戏手柄测试程序" + " "*15 + "║")
        print("╚" + "═"*58 + "╝")
        print()

        # 显示手柄信息
        if self.joystick:
            print(f"📋 手柄: {self.joystick.get_name()}")
        print()

        # 显示车辆控制信号
        print("🚗 车辆控制信号")
        print("─"*60)

        throttle = control_signal['throttle']
        steer = control_signal['steer']
        brake = control_signal['brake']
        hand_brake = control_signal['hand_brake']

        # 油门条
        throttle_bar = self._create_bar(throttle, width=30, char='█')
        print(f"  油门 (RT):  [{throttle_bar}] {throttle:5.2f}")

        # 刹车条
        brake_bar = self._create_bar(brake, width=30, char='█')
        print(f"  刹车 (LT):  [{brake_bar}] {brake:5.2f}")

        # 转向条
        steer_bar = self._create_steer_bar(steer, width=30)
        steer_dir = "左转" if steer < -0.05 else "右转" if steer > 0.05 else "直行"
        print(f"  转向 (LS):  [{steer_bar}] {steer:+5.2f} ({steer_dir})")

        # 手刹
        hand_brake_status = "🔴 启用" if hand_brake else "⚪ 关闭"
        print(f"  手刹 (A):   {hand_brake_status}")

        print()

        # 显示原始手柄数据
        print("🎮 原始手柄数据")
        print("─"*60)

        # 显示所有轴
        if self.joystick:
            num_axes = self.joystick.get_numaxes()
            print("  轴:")
            for i in range(num_axes):
                raw_value = self.joystick.get_axis(i)
                print(f"    轴 {i}: {raw_value:+6.3f}", end="  ")
                if (i + 1) % 3 == 0:
                    print()
            if num_axes % 3 != 0:
                print()

            print()

            # 显示按钮状态
            num_buttons = self.joystick.get_numbuttons()
            pressed_buttons = [i for i in range(num_buttons) if self.get_button_state(i)]

            if pressed_buttons:
                print(f"  按下的按钮: {', '.join(map(str, pressed_buttons))}")
            else:
                print("  按下的按钮: 无")

        print()
        print("─"*60)
        print("💡 提示: 按 ESC 或 Ctrl+C 退出")
        print()

    def _create_bar(self, value: float, width: int = 30, char: str = '█') -> str:
        """
        创建进度条

        Args:
            value: 值 (0.0 - 1.0)
            width: 进度条宽度
            char: 填充字符

        Returns:
            str: 进度条字符串
        """
        filled = int(value * width)
        empty = width - filled
        return char * filled + ' ' * empty

    def _create_steer_bar(self, value: float, width: int = 30) -> str:
        """
        创建转向条（中心对称）

        Args:
            value: 转向值 (-1.0 - 1.0)
            width: 进度条宽度

        Returns:
            str: 转向条字符串
        """
        center = width // 2
        if value < 0:  # 左转
            filled = int(abs(value) * center)
            start = center - filled
            bar = ' ' * start + '◄' * filled + '│' + ' ' * center
        elif value > 0:  # 右转
            filled = int(value * center)
            bar = ' ' * center + '│' + '►' * filled + ' ' * (center - filled)
        else:  # 直行
            bar = ' ' * center + '│' + ' ' * center

        return bar

    def run(self):
        """运行测试主循环"""
        if not self.connect_gamepad():
            return

        print("开始读取手柄输入...")
        print("按 ESC 键或 Ctrl+C 退出\n")
        time.sleep(2)

        clock = pygame.time.Clock()

        try:
            while self.running:
                # 处理 pygame 事件
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.running = False

                # 获取控制信号
                control_signal = self.get_vehicle_control_signal()

                # 显示状态
                self.print_status(control_signal)

                # 限制刷新率为 20 FPS
                clock.tick(20)

        except KeyboardInterrupt:
            print("\n\n收到中断信号，正在退出...")

        finally:
            self.cleanup()

    def cleanup(self):
        """清理资源"""
        if self.joystick:
            self.joystick.quit()
        pygame.quit()
        print("\n✅ 程序已退出")


def main():
    """主函数"""
    print("\n" + "="*60)
    print("  游戏手柄测试程序")
    print("="*60)
    print("\n请确保已连接游戏手柄...")
    print()

    tester = GamepadTester()
    tester.run()


if __name__ == '__main__':
    main()
