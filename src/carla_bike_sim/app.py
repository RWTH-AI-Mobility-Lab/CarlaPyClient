import sys
from PySide6.QtWidgets import QApplication
from carla_bike_sim.gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.resize(1200, 800)
    window.show()

    app.exec()


if __name__ == "__main__":
    main()
