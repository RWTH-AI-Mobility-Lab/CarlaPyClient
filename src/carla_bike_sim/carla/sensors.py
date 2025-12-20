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
        # TODO: bugfix while destroy cams
        if self.front_camera is not None:
            self.front_camera.stop()
            self.front_camera.destroy()
            self.front_camera = None
        if self.rear_camera is not None:
            self.rear_camera.stop()
            self.rear_camera.destroy()
            self.rear_camera = None
        if self.left_camera is not None:
            self.left_camera.stop()
            self.left_camera.destroy()
            self.left_camera = None
        if self.right_camera is not None:
            self.right_camera.stop()
            self.right_camera.destroy()
            self.right_camera = None
    
    def camera_callback(self, image: carla.Image, camera_position: str):
        try:
            bgr_image = carla_image_to_bgr(image)

            if camera_position == 'front':
                self.front_camera_image_ready.emit(bgr_image)
            elif camera_position == 'rear':
                self.rear_camera_image_ready.emit(bgr_image)
            elif camera_position == 'left':
                self.left_camera_image_ready.emit(bgr_image)
            elif camera_position == 'right':
                self.right_camera_image_ready.emit(bgr_image)
        except Exception as e:
            print(f"Error in camera callback ({camera_position}): {e}")