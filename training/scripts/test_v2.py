import sys, os
import ultralytics
sys.modules['ultralytics.yolo'] = ultralytics
sys.modules['ultralytics.yolo.utils'] = ultralytics.utils
from ultralytics.utils import tal
sys.modules['ultralytics.yolo.utils.tal'] = tal

from ultralytics import YOLO
import cv2

# 注入 C2fNAM
import importlib, ultralytics.nn.modules as m
spec = importlib.util.spec_from_file_location("cm", "ultralytics1/nn/modules.py")
cm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cm)
for n in ["C2fNAM","NAMAttention","Channel_Att"]:
    setattr(m, n, getattr(cm, n))

model = YOLO("runs/segment/strawberry-v2/weights/best.pt")

test_dir = r"C:\Users\tttjw\Desktop\code\atlas200\datasets\strawdi\val\images"
out_dir = "runs/segment/strawberry-v2/test_samples"
os.makedirs(out_dir, exist_ok=True)

imgs = sorted(os.listdir(test_dir))[:6]
for fname in imgs:
    path = os.path.join(test_dir, fname)
    results = model(path, conf=0.25, iou=0.45)[0]
    boxes = results.boxes
    if boxes is not None:
        print(f"{fname}: {len(boxes)} detections")
        for i, (cls, conf) in enumerate(zip(boxes.cls.tolist(), boxes.conf.tolist())):
            print(f"  [{i}] Strawberry {conf:.3f}")
    else:
        print(f"{fname}: 0 detections")
    r = results.plot()
    cv2.imwrite(os.path.join(out_dir, fname), r)
print("Done! Saved to test_samples/")
