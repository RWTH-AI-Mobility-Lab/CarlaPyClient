import carla
import numpy as np
import cv2 as cv
from typing import Optional, Callable
from PySide6.QtCore import QObject, Signal, QThread


class CarlaClientManager(QObject):
    """CARLA 客户端管理器类

    Signals:
        connection_status_changed(bool, str): 连接状态变化 (已连接, 消息)
        camera_image_ready(np.ndarray): 摄像头图像准备就绪
        simulation_error(str): 仿真错误信息
    """

    connection_status_changed = Signal(bool, str)
    camera_image_ready = Signal(np.ndarray)
    simulation_error = Signal(str)

    def __init__(self, host: str = 'localhost', port: int = 2000, timeout: float = 5.0):
        super().__init__()
        self.host = host
        self.port = port
        self.timeout = timeout

        self.client: Optional[carla.Client] = None
        self.world: Optional[carla.World] = None
        self.vehicle: Optional[carla.Vehicle] = None
        self.camera: Optional[carla.Sensor] = None
        self.spectator: Optional[carla.Actor] = None

        self._is_connected = False
        self._is_running = False

        self.simulation_thread: Optional[SimulationThread] = None

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @property
    def is_running(self) -> bool:
        return self._is_running

    def connect(self) -> bool:
        try:
            self.client = carla.Client(self.host, self.port)
            self.client.set_timeout(self.timeout)

            version = self.client.get_server_version()
            self._is_connected = True

            message = f"Connected to CARLA server version: {version}"
            self.connection_status_changed.emit(True, message)
            return True

        except Exception as e:
            error_msg = f"Failed to connect to CARLA server: {str(e)}"
            self.connection_status_changed.emit(False, error_msg)
            self.simulation_error.emit(error_msg)
            return False

    def disconnect(self):
        """断开与 CARLA 服务器的连接并清理资源"""
        self.stop_simulation()

        if self.camera is not None:
            self.camera.stop()
            self.camera.destroy()
            self.camera = None

        if self.vehicle is not None:
            self.vehicle.destroy()
            self.vehicle = None

        self.world = None
        self.client = None
        self.spectator = None
        self._is_connected = False

        self.connection_status_changed.emit(False, "Disconnected from CARLA server")

    def start_simulation(self,
                        map_name: Optional[str] = None,
                        vehicle_blueprint: str = "vehicle.audi.a2",
                        camera_width: int = 800,
                        camera_height: int = 600) -> bool:
        if not self._is_connected:
            self.simulation_error.emit("Not connected to CARLA server")
            return False

        if self._is_running:
            self.simulation_error.emit("Simulation is already running")
            return False

        try:
            if map_name is None:
                map_name = self.client.get_available_maps()[0]
            self.world = self.client.load_world(map_name)

            bp = self.world.get_blueprint_library().find(vehicle_blueprint)
            spawn_point = self.world.get_map().get_spawn_points()[0]
            self.vehicle = self.world.spawn_actor(bp, spawn_point)
            
            self.spectator = self.world.get_spectator()
            self.spectator.set_transform(carla.Transform(
                carla.Location(x=spawn_point.location.x , y=spawn_point.location.y-5, z=spawn_point.location.z + 2),
                carla.Rotation(pitch=-15.0, yaw=spawn_point.rotation.yaw)
            ))

            vehicle_control = carla.VehicleControl()
            vehicle_control.throttle = 0.5
            self.vehicle.apply_control(vehicle_control)

            self._setup_camera(camera_width, camera_height)

            self.simulation_thread = SimulationThread(self.world)
            self.simulation_thread.start()

            self._is_running = True
            return True

        except Exception as e:
            error_msg = f"Failed to start simulation: {str(e)}"
            self.simulation_error.emit(error_msg)
            return False

    def stop_simulation(self):
        if self.simulation_thread is not None:
            self.simulation_thread.stop()
            self.simulation_thread.wait()
            self.simulation_thread = None

        if self.camera is not None:
            self.camera.stop()

        self._is_running = False

    def _setup_camera(self, width: int, height: int):
        camera_bp = self.world.get_blueprint_library().find("sensor.camera.rgb")
        camera_bp.set_attribute("image_size_x", str(width))
        camera_bp.set_attribute("image_size_y", str(height))

        camera_transform = carla.Transform(
            carla.Location(x=-5.5, z=2.4),
            carla.Rotation(pitch=-15.0)
        )

        self.camera = self.world.spawn_actor(
            camera_bp,
            camera_transform,
            attach_to=self.vehicle
        )

        self.camera.listen(self._camera_callback)

    def _camera_callback(self, image: carla.Image):
        """摄像头图像回调函数

        Args:
            image: CARLA 图像对象
        """
        try:
            # 处理图像数据
            img_array = np.frombuffer(image.raw_data, dtype=np.uint8)
            img_array = img_array.reshape((image.height, image.width, 4))
            img_bgr = img_array[:, :, :3]  # 只取 BGR 通道

            # 发送信号（注意：这里是 BGR 格式，GUI 中需要转换为 Qt 格式）
            self.camera_image_ready.emit(img_bgr)

        except Exception as e:
            self.simulation_error.emit(f"Camera callback error: {str(e)}")

    def set_vehicle_control(self, throttle: float = 0.0, steer: float = 0.0,
                           brake: float = 0.0, hand_brake: bool = False):
        """设置车辆完整控制

        Args:
            throttle: 油门 (0.0 到 1.0)
            steer: 转向 (-1.0 到 1.0)
            brake: 刹车 (0.0 到 1.0)
            hand_brake: 手刹
        """
        if self.vehicle is not None:
            control = carla.VehicleControl()
            control.throttle = max(0.0, min(1.0, throttle))
            control.steer = max(-1.0, min(1.0, steer))
            control.brake = max(0.0, min(1.0, brake))
            control.hand_brake = hand_brake
            self.vehicle.apply_control(control)

    def get_vehicle_transform(self) -> Optional[carla.Transform]:
        if self.vehicle is not None:
            return self.vehicle.get_transform()
        return None

    def get_vehicle_velocity(self) -> Optional[carla.Vector3D]:
        if self.vehicle is not None:
            return self.vehicle.get_velocity()
        return None


class SimulationThread(QThread):
    def __init__(self, world: carla.World):
        super().__init__()
        self.world = world
        self._running = True

    def run(self):
        while self._running:
            try:
                self.world.tick()
            except Exception as e:
                print(f"Simulation tick error: {e}")
                break

    def stop(self):
        self._running = False
