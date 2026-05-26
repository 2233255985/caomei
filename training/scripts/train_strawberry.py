"""训练草莓分割模型 — 迁移学习

策略：训练时用标准 C2f（parse_model 原生支持通道跟踪），
      C2f 与 C2fNAM 共享 cv1/cv2/m 权重（C2fNAM 只多 m1 注意力模块），
      导出 ONNX 时再注入 C2fNAM。
"""
import sys, os, importlib.util, copy

PROJECT_DIR = r"C:\Users\tttjw\Desktop\code\atlas200\ultralytics-v8.0.45-relu6-tomato-seg"
os.chdir(PROJECT_DIR)

# 兼容层
import ultralytics
sys.modules['ultralytics.yolo'] = ultralytics
sys.modules['ultralytics.yolo.utils'] = ultralytics.utils
from ultralytics.utils import tal
sys.modules['ultralytics.yolo.utils.tal'] = tal

# 先注入 C2fNAM（基模型 best.pt 加载时需要反序列化 C2fNAM 模块）
spec = importlib.util.spec_from_file_location("cm", "ultralytics1/nn/modules.py")
cm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cm)
import ultralytics.nn.modules as m
for n in ['C2fNAM', 'NAMAttention', 'Channel_Att']:
    setattr(m, n, getattr(cm, n))
import ultralytics.nn as nn
for n in ['C2fNAM', 'NAMAttention', 'Channel_Att']:
    setattr(nn.modules, n, getattr(cm, n))

from ultralytics import YOLO
import torch

if __name__ == '__main__':
    # 1. 加载基模型 best.pt（需要 C2fNAM 已注入才能反序列化）
    model = YOLO(r"runs\segment\train19\weights\best.pt")

    # 2. 修改模型 yaml：C2fNAM → C2f（parse_model 原生支持）
    #    训练完导出 ONNX 时再换回 C2fNAM
    yaml = model.model.yaml
    for section in ['backbone', 'head']:
        for layer in yaml.get(section, []):
            if len(layer) >= 3 and layer[2] == 'C2fNAM':
                layer[2] = 'C2f'
                if len(layer[3]) == 1:
                    layer[3].append(False)  # C2f 需要 shortcut 参数
    model.model.yaml = yaml

    # 3. 训练
    results = model.train(
        data=r"C:\Users\tttjw\Desktop\code\atlas200\datasets\strawdi\data.yaml",
        epochs=100,
        batch=16,
        imgsz=640,
        lr0=0.005,
        lrf=0.01,
        optimizer='SGD',
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3.0,
        workers=4,
        close_mosaic=10,
        device=0,
        amp=True,
        project='runs/segment',
        name='strawberry-v2',
        exist_ok=True,
    )
