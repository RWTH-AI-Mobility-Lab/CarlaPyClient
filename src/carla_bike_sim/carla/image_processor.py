import threading
import queue
from typing import Optional
import carla
import numpy as np
from PySide6.QtCore import QObject, Signal

from carla_bike_sim.carla.utils import carla_image_to_bgr


class ImageProcessorWorker(QObject):
    image_ready = Signal(np.ndarray)

    def __init__(self, camera_name: str, max_queue_size: int = 2):
        super().__init__()
        self.camera_name = camera_name
        self.image_queue: queue.Queue = queue.Queue(maxsize=max_queue_size)
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._frame_dropped_count = 0

    def start(self):
        if self._thread is not None and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._process_loop,
            name=f"ImageProcessor-{self.camera_name}",
            daemon=True
        )
        self._thread.start()

    def stop(self):
        self._stop_event.set()

        try:
            while not self.image_queue.empty():
                self.image_queue.get_nowait()
        except queue.Empty:
            pass

        if self._thread is not None and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def enqueue_image(self, image: carla.Image) -> bool:
        try:
            self.image_queue.put_nowait(image)
            return True
        except queue.Full:
            try:
                self.image_queue.get_nowait()  # drop oldest frame
                self.image_queue.put_nowait(image)
                self._frame_dropped_count += 1
                return True
            except (queue.Full, queue.Empty):
                return False

    def _process_loop(self):
        while not self._stop_event.is_set():
            try:
                if self._stop_event.is_set():
                    break
                
                image = self.image_queue.get(timeout=0.1)
                bgr_image = carla_image_to_bgr(image)
                self.image_ready.emit(bgr_image)
            except queue.Empty:
                continue
            except Exception as e:
                if not self._stop_event.is_set():
                    print(f"[{self.camera_name}] Error while processing image: {e}")
                    
# debug msg

    def get_queue_size(self) -> int:
        return self.image_queue.qsize()

    def get_dropped_frames(self) -> int:
        return self._frame_dropped_count
