import carla
import numpy as np
import threading
from typing import Optional, Dict
from PySide6.QtCore import QObject, Signal
from carla_bike_sim.carla.image_processor import ImageProcessorWorker

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
        self._lock = threading.RLock()

        self._image_workers: Dict[str, ImageProcessorWorker] = {}
    
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

        self._setup_camera_worker('front', camera_bp, vehicle, world,
                                   carla.Transform(carla.Location(x=1.5, z=2.4)))
        self._setup_camera_worker('rear', camera_bp, vehicle, world,
                                   carla.Transform(carla.Location(x=-1.5, z=2.4), carla.Rotation(yaw=180)))
        self._setup_camera_worker('left', camera_fisheye_bp, vehicle, world,
                                   carla.Transform(carla.Location(y=-1.5, z=2.4), carla.Rotation(yaw=-90)))
        self._setup_camera_worker('right', camera_fisheye_bp, vehicle, world,
                                   carla.Transform(carla.Location(y=1.5, z=2.4), carla.Rotation(yaw=90)))

    def _setup_camera_worker(self, camera_name: str, camera_bp, vehicle, world, transform):
        worker = ImageProcessorWorker(camera_name=camera_name, max_queue_size=2)
        self._image_workers[camera_name] = worker

        signal_map = {
            'front': self.front_camera_image_ready,
            'rear': self.rear_camera_image_ready,
            'left': self.left_camera_image_ready,
            'right': self.right_camera_image_ready,
        }
        worker.image_ready.connect(signal_map[camera_name])

        worker.start()

        camera = world.spawn_actor(camera_bp, transform, attach_to=vehicle)
        camera.listen(lambda image: self._camera_callback(image, camera_name))

        setattr(self, f'{camera_name}_camera', camera)
    
    def destroy_cameras(self):
        with self._lock:
            self._destroying = True
        
        # 定义所有摄像头及其名称
        cameras = [
            ('front', 'front_camera'),
            ('rear', 'rear_camera'),
            ('left', 'left_camera'),
            ('right', 'right_camera')
        ]

        # 1. 先停止所有摄像头的数据采集
        for name, attr_name in cameras:
            camera = getattr(self, attr_name)
            if camera is not None:
                try:
                    camera.stop()
                except Exception as e:
                    print(f"Error stopping {name} camera: {e}")

        # 2. 停止所有图像处理工作线程
        for name, worker in self._image_workers.items():
            try:
                worker.stop()
            except Exception as e:
                print(f"Error stopping {name} worker: {e}")

        # 3. 销毁所有摄像头
        for name, attr_name in cameras:
            camera = getattr(self, attr_name)
            if camera is not None:
                try:
                    camera.destroy()
                except Exception as e:
                    print(f"Error destroying {name} camera: {e}")
                finally:
                    setattr(self, attr_name, None)

        self._image_workers.clear()

        with self._lock:
            self._destroying = False
    
    def _camera_callback(self, image: carla.Image, camera_name: str):
        with self._lock:
            if self._destroying:
                return

        worker = self._image_workers.get(camera_name)
        if worker is None:
            return

        try:
            worker.enqueue_image(image)
        except Exception as e:
            with self._lock:
                if not self._destroying:
                    print(f"Error enqueueing image for {camera_name}: {e}")

    def get_performance_stats(self) -> dict:
        stats = {}
        for name, worker in self._image_workers.items():
            stats[name] = {
                'queue_size': worker.get_queue_size(),
                'dropped_frames': worker.get_dropped_frames()
            }
        return stats