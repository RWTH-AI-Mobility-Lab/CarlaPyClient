"""
CARLA Bike Simulator Configuration
集中管理应用程序中的常量和配置参数
"""

# =============================================================================
# CARLA 连接配置
# =============================================================================

# 默认连接参数
DEFAULT_CARLA_HOST = 'localhost'
DEFAULT_CARLA_PORT = 2000
DEFAULT_CARLA_TIMEOUT = 5.0  # 秒

# 端口验证范围
PORT_MIN = 1
PORT_MAX = 65535


# =============================================================================
# 仿真配置
# =============================================================================

# 默认车辆蓝图
DEFAULT_VEHICLE_BLUEPRINT = 'vehicle.bh.crossbike'

# 默认地图 (None表示使用服务器的第一个可用地图)
DEFAULT_MAP_NAME = None

# 车辆控制参数
DEFAULT_THROTTLE = 0.5  # 启动时的默认油门 (0.0 - 1.0)

# 观察者摄像机位置偏移 (相对于车辆spawn点)
SPECTATOR_OFFSET_X = 0.0
SPECTATOR_OFFSET_Y = -5.0  # 车辆后方5米
SPECTATOR_OFFSET_Z = 2.0   # 高度2米
SPECTATOR_PITCH = -15.0    # 向下倾斜15度


# =============================================================================
# 摄像头传感器配置
# =============================================================================

# 摄像头分辨率
CAMERA_IMAGE_WIDTH = 800
CAMERA_IMAGE_HEIGHT = 600

# 摄像头视野角度 (Field of View)
CAMERA_FOV = 90

# 摄像头位置配置 (相对于车辆中心)
# 格式: (x, y, z, yaw, pitch, roll)

# 前置摄像头
FRONT_CAMERA_X = 1.5
FRONT_CAMERA_Y = 0.0
FRONT_CAMERA_Z = 2.4
FRONT_CAMERA_YAW = 0.0
FRONT_CAMERA_PITCH = 0.0
FRONT_CAMERA_ROLL = 0.0

# 后置摄像头
REAR_CAMERA_X = -1.5
REAR_CAMERA_Y = 0.0
REAR_CAMERA_Z = 2.4
REAR_CAMERA_YAW = 180.0
REAR_CAMERA_PITCH = 0.0
REAR_CAMERA_ROLL = 0.0

# 左侧摄像头
LEFT_CAMERA_X = 0.0
LEFT_CAMERA_Y = -1.5
LEFT_CAMERA_Z = 2.4
LEFT_CAMERA_YAW = -90.0
LEFT_CAMERA_PITCH = 0.0
LEFT_CAMERA_ROLL = 0.0

# 右侧摄像头
RIGHT_CAMERA_X = 0.0
RIGHT_CAMERA_Y = 1.5
RIGHT_CAMERA_Z = 2.4
RIGHT_CAMERA_YAW = 90.0
RIGHT_CAMERA_PITCH = 0.0
RIGHT_CAMERA_ROLL = 0.0


# =============================================================================
# GUI 配置
# =============================================================================

# 主窗口
MAIN_WINDOW_TITLE = "CARLA Bicycle Simulator"
MAIN_WINDOW_WIDTH = 1200
MAIN_WINDOW_HEIGHT = 800

# 控制面板默认值
CONTROL_PANEL_DEFAULT_HOST = DEFAULT_CARLA_HOST
CONTROL_PANEL_DEFAULT_PORT = str(DEFAULT_CARLA_PORT)
CONTROL_PANEL_PORT_INPUT_MAX_WIDTH = 100

# 状态栏消息
STATUS_READY = "Ready"
STATUS_CONNECTING = "Connecting to {}:{}..."
STATUS_CONNECTED = "Connected to CARLA server version: {}"
STATUS_DISCONNECTING = "Disconnecting from CARLA server..."
STATUS_DISCONNECTED = "Disconnected from CARLA server"
STATUS_STARTING_SIMULATION = "Starting simulation..."
STATUS_SIMULATION_STARTED = "Simulation started"
STATUS_STOPPING_SIMULATION = "Stopping simulation..."
STATUS_SIMULATION_STOPPED = "Simulation stopped"
STATUS_ERROR = "Error: {}"

# 占位符文本
PLACEHOLDER_WAITING = "Waiting for CARLA connection..."
PLACEHOLDER_DISCONNECTED = "Disconnected from CARLA server"
PLACEHOLDER_STOPPED = "Simulation stopped"

# 摄像头视图标签
CAMERA_LABEL_FRONT = "Front Camera"
CAMERA_LABEL_REAR = "Rear Camera"
CAMERA_LABEL_LEFT = "Left Camera"
CAMERA_LABEL_RIGHT = "Right Camera"


# =============================================================================
# 车辆控制限制
# =============================================================================

# 油门、刹车、转向的取值范围
THROTTLE_MIN = 0.0
THROTTLE_MAX = 1.0

BRAKE_MIN = 0.0
BRAKE_MAX = 1.0

STEER_MIN = -1.0
STEER_MAX = 1.0


# =============================================================================
# 错误消息
# =============================================================================

# 连接错误
ERROR_CONNECTION_FAILED = "Failed to connect to CARLA server: {}"
ERROR_NOT_CONNECTED = "Not connected to CARLA server"
ERROR_ALREADY_CONNECTED = "Already connected to CARLA server"

# 仿真错误
ERROR_SIMULATION_START_FAILED = "Failed to start simulation: {}"
ERROR_SIMULATION_ALREADY_RUNNING = "Simulation is already running"
ERROR_SIMULATION_NOT_RUNNING = "Simulation is not running"

# 输入验证错误
ERROR_INVALID_HOST = "Host cannot be empty."
ERROR_INVALID_PORT = "Port must be a number between {} and {}."


# =============================================================================
# 调试配置
# =============================================================================

# 是否启用调试日志
DEBUG_MODE = False

# 是否在控制台打印传感器回调错误
PRINT_SENSOR_ERRORS = True
