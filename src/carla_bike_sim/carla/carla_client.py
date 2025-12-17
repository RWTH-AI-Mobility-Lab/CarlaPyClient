import carla
import cv2 as cv
import numpy as np

def process_image(image):
    img_array = np.frombuffer(image.raw_data, dtype=np.uint8)
    img_array = img_array.reshape((image.height, image.width, 4))
    img_rgb = img_array[:, :, :3]  # only RGB
    img_bgr = cv.cvtColor(img_rgb, cv.COLOR_RGB2BGR)
    return img_bgr

def camera_callback(image):
    img = process_image(image)
    cv.imshow("Camera View", img)
    cv.waitKey(10)

client = carla.Client('localhost', 2000)
client.set_timeout(5.0)
print("Connected to CARLA server version:", client.get_server_version())

map_name = client.get_available_maps()[0]
world = client.load_world(map_name)
print("Loaded map:", map_name)

bp = world.get_blueprint_library().find("vehicle.audi.a2")
spawn_point = world.get_map().get_spawn_points()[0]
vehicle = world.spawn_actor(bp, spawn_point)

vehicleControl = carla.VehicleControl()
vehicleControl.throttle = 0.5

vehicle.apply_control(vehicleControl)

camera_bp = world.get_blueprint_library().find("sensor.camera.rgb")
camera_bp.set_attribute("image_size_x", "800")
camera_bp.set_attribute("image_size_y", "600")
camera_transform = carla.Transform(carla.Location(x=-5.5, z=2.4), carla.Rotation(pitch=-15.0))
camera = world.spawn_actor(camera_bp, camera_transform, attach_to=vehicle)

camera.listen(camera_callback)

while True:
    world.tick()
    