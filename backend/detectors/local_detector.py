"""本地 ONNX Runtime 推理封装"""
import os
import cv2
from .yolo_seg import YOLOv8SegEngine


class LocalDetector:
    def __init__(self, model_path, conf=0.25, iou=0.45):
        self.model_path = model_path
        self.conf = conf
        self.iou = iou
        self._engine = None

    def _ensure_engine(self):
        if self._engine is None:
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f'模型文件不存在: {self.model_path}')
            self._engine = YOLOv8SegEngine(self.model_path, conf=self.conf, iou=self.iou)
        return self._engine

    def detect(self, image_input):
        """接受文件路径字符串或 numpy 数组 (BGR image)"""
        if isinstance(image_input, str):
            img = cv2.imread(image_input)
            if img is None:
                raise ValueError(f'无法读取图片: {image_input}')
        else:
            img = image_input  # 已经是 numpy 数组
        engine = self._ensure_engine()
        return engine.detect(img)

    def is_available(self):
        return os.path.exists(self.model_path)
