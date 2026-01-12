import carla
import numpy as np
import cv2 as cv
from typing import Optional
from PySide6.QtCore import QObject, Signal
from carla_bike_sim.carla.sensor_manager import SensorManager
from carla_bike_sim.control.vehicle_control_signal import VehicleControlSignal

class CarlaClientManager(QObject):
    connection_status_changed = Signal(bool, str)
    simulation_error = Signal(str)

    def __init__(self, host: str = 'localhost', port: int = 2000, timeout: float = 10.0):
        super().__init__()
        self.host = host
        self.port = port
        self.timeout = timeout

        self.client: Optional[carla.Client] = None
        self.world: Optional[carla.World] = None
        self.vehicle: Optional[carla.Vehicle] = None
        self.spectator: Optional[carla.Actor] = None
        
        self.sensor_manager = SensorManager()

        self._is_connected = False
        self._is_running = False

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
        self.stop_simulation()

        if self.sensor_manager is not None:
            self.sensor_manager.destroy_cameras()

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
                        vehicle_blueprint: str = "vehicle.audi.a2") -> bool:
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
            
            settings = self.world.get_settings()
            print("sync:", settings.synchronous_mode)
            print("fixed_dt:", settings.fixed_delta_seconds)

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

            self.sensor_manager.setup_cameras(self.vehicle, self.world)

            self._is_running = True
            return True

        except Exception as e:
            error_msg = f"Failed to start simulation: {str(e)}"
            self.simulation_error.emit(error_msg)
            return False

    def stop_simulation(self):
        if not self._is_running:
            return

        if self.sensor_manager is not None:
            self.sensor_manager.destroy_cameras()

        if self.vehicle is not None:
            self.vehicle.destroy()
            self.vehicle = None

        self.world = None
        self.spectator = None
        self._is_running = False
        
    def get_vehicle_control_state(self) -> Optional[VehicleControlSignal]:
        if self.vehicle is None:
            return None
        control = self.vehicle.get_control()
        return VehicleControlSignal(
            throttle=control.throttle,
            brake=control.brake,
            steer=control.steer,
            gear=control.gear
        )

    def set_vehicle_control(self, throttle: float = 0.0, steer: float = 0.0,
                           brake: float = 0.0, hand_brake: bool = False):
        """
        Args:
            throttle:(0.0 to 1.0)
            steer: (-1.0 to 1.0)
            brake: (0.0 to 1.0)
            hand_brake: bool
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
