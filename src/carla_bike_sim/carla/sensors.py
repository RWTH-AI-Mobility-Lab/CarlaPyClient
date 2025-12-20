import carla
import numpy as np
from typing import Optional
from PySide6.QtCore import QObject, Signal
from carla_bike_sim.carla.utils import carla_image_to_bgr

class SensorManager(QObject):
    # Signals:
    front_camera_image_ready = Signal(np.ndarray)
    rear_camera_image_ready = Signal(np.ndarray)
    left_camera_image_ready = Signal(np.ndarray)
    right_camera_image_ready = Signal(np.ndarray)

    def __init__(self):
        super().__init__()
        self.front_camera: Optional[carla.Sensor] = None
        self.rear_camera: Optional[carla.Sensor] = None
        self.left_camera: Optional[carla.Sensor] = None
        self.right_camera: Optional[carla.Sensor] = None
        self._destroying = False  # 标志位，防止销毁时回调继续执行
    
    def setup_cameras(self, vehicle: carla.Vehicle, world: carla.World):
        blueprint_library = world.get_blueprint_library()
        
        camera_bp = blueprint_library.find('sensor.camera.rgb')
        camera_bp.set_attribute('image_size_x', '800')
        camera_bp.set_attribute('image_size_y', '600')
        camera_bp.set_attribute('fov', '90')
        
        camera_fisheye_bp = blueprint_library.find('sensor.camera.rgb')
        camera_fisheye_bp.set_attribute('image_size_x', '800')
        camera_fisheye_bp.set_attribute('image_size_y', '600')
        camera_fisheye_bp.set_attribute('fov', '160')
        
        # Front camera
        transform_front = carla.Transform(carla.Location(x=1.5, z=2.4))
        self.front_camera = world.spawn_actor(camera_bp, transform_front, attach_to=vehicle)
        self.front_camera.listen(lambda image: self.camera_callback(image, 'front'))

        # Rear camera
        transform_rear = carla.Transform(carla.Location(x=-1.5, z=2.4), carla.Rotation(yaw=180))
        self.rear_camera = world.spawn_actor(camera_bp, transform_rear, attach_to=vehicle)
        self.rear_camera.listen(lambda image: self.camera_callback(image, 'rear'))

        # Left camera
        transform_left = carla.Transform(carla.Location(y=-1.5, z=2.4), carla.Rotation(yaw=-90))
        self.left_camera = world.spawn_actor(camera_fisheye_bp, transform_left, attach_to=vehicle)
        self.left_camera.listen(lambda image: self.camera_callback(image, 'left'))

        # Right camera
        transform_right = carla.Transform(carla.Location(y=1.5, z=2.4), carla.Rotation(yaw=90))
        self.right_camera = world.spawn_actor(camera_fisheye_bp, transform_right, attach_to=vehicle)
        self.right_camera.listen(lambda image: self.camera_callback(image, 'right'))
    
    def destroy_cameras(self):
        """安全地销毁所有摄像头"""
        # 设置标志位，防止新的回调执行
        self._destroying = True
        
        # 定义所有摄像头及其名称
        cameras = [
            ('front', 'front_camera'),
            ('rear', 'rear_camera'),
            ('left', 'left_camera'),
            ('right', 'right_camera')
        ]
        
        # 先停止所有摄像头，防止新回调
        for name, attr_name in cameras:
            camera = getattr(self, attr_name)
            if camera is not None:
                try:
                    camera.stop()
                except Exception as e:
                    print(f"Error stopping {name} camera: {e}")
        
        # 等待一小段时间，让正在执行的回调完成
        import time
        time.sleep(0.1)
        
        # 然后销毁所有摄像头
        for name, attr_name in cameras:
            camera = getattr(self, attr_name)
            if camera is not None:
                try:
                    camera.destroy()
                except Exception as e:
                    print(f"Error destroying {name} camera: {e}")
                finally:
                    setattr(self, attr_name, None)
        
        # 重置标志位
        self._destroying = False
    
    def camera_callback(self, image: carla.Image, camera_position: str):
        """摄像头回调函数 - 在 CARLA 后台线程中执行"""
        # 如果正在销毁，直接返回，避免访问已销毁的对象
        if self._destroying:
            return
        
        try:
            bgr_image = carla_image_to_bgr(image)
            
            # 再次检查，防止在图像处理过程中开始销毁
            if self._destroying:
                return

            if camera_position == 'front':
                self.front_camera_image_ready.emit(bgr_image)
            elif camera_position == 'rear':
                self.rear_camera_image_ready.emit(bgr_image)
            elif camera_position == 'left':
                self.left_camera_image_ready.emit(bgr_image)
            elif camera_position == 'right':
                self.right_camera_image_ready.emit(bgr_image)
        except Exception as e:
            # 忽略销毁过程中的错误
            if not self._destroying:
                print(f"Error in camera callback ({camera_position}): {e}")