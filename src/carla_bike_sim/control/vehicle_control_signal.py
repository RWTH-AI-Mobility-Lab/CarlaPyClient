from dataclasses import dataclass


@dataclass
class VehicleControlSignal:
    throttle: float = 0.0
    steer: float = 0.0
    brake: float = 0.0
    hand_brake: bool = False
    gear: int = 0  # -1:倒车, 0:空挡, 1:前进

    def clamp(self) -> 'VehicleControlSignal':
        self.throttle = max(0.0, min(1.0, self.throttle))
        self.steer = max(-1.0, min(1.0, self.steer))
        self.brake = max(0.0, min(1.0, self.brake))
        return self

    def reset(self) -> None:
        self.throttle = 0.0
        self.steer = 0.0
        self.brake = 0.0
        self.hand_brake = False
        self.gear = 0

    def __str__(self) -> str:
        return (f"VehicleControlSignal(throttle={self.throttle:.2f}, "
                f"steer={self.steer:.2f}, brake={self.brake:.2f}, "
                f"hand_brake={self.hand_brake}, gear={self.gear})")

    def copy(self) -> 'VehicleControlSignal':
        return VehicleControlSignal(
            throttle=self.throttle,
            steer=self.steer,
            brake=self.brake,
            hand_brake=self.hand_brake,
            gear=self.gear
        )
