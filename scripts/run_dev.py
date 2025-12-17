import os
import sys
from pathlib import Path


def main():
    project_root = Path(__file__).resolve().parent.parent

    src_path = project_root / "src"
    sys.path.insert(0, str(src_path))

    from carla_bike_sim.app import main as app_main

    app_main()


if __name__ == "__main__":
    main()
