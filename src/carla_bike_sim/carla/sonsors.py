import carla
from typing import Optional

class SensorManager:
    def __init__(self):
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

        # Front camera
        transform_front = carla.Transform(carla.Location(x=1.5, z=2.4))
        self.front_camera = world.spawn_actor(camera_bp, transform_front, attach_to=vehicle)

        # Rear camera
        transform_rear = carla.Transform(carla.Location(x=-1.5, z=2.4), carla.Rotation(yaw=180))
        self.rear_camera = world.spawn_actor(camera_bp, transform_rear, attach_to=vehicle)

        # Left camera
        transform_left = carla.Transform(carla.Location(y=-1.5, z=2.4), carla.Rotation(yaw=-90))
        self.left_camera = world.spawn_actor(camera_bp, transform_left, attach_to=vehicle)

        # Right camera
        transform_right = carla.Transform(carla.Location(y=1.5, z=2.4), carla.Rotation(yaw=90))
        self.right_camera = world.spawn_actor(camera_bp, transform_right, attach_to=vehicle)