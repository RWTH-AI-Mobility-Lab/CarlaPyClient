import carla
import numpy as np

def carla_image_to_bgr(image: carla.Image) -> np.ndarray:
    """将 CARLA 图像转换为 BGR 格式的 numpy 数组"""
    img_array = np.frombuffer(image.raw_data, dtype=np.uint8)
    img_array = img_array.reshape((image.height, image.width, 4))
    img_bgr = img_array[:, :, :3]
    return img_bgr