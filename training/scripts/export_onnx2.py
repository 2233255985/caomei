"""导出 ONNX —— 注入 C2fNAM + 补 _built"""
import sys, os, importlib.util

PROJECT_DIR = r"C:\Users\tttjw\Desktop\code\atlas200\ultralytics-v8.0.45-relu6-tomato-seg"
os.chdir(PROJECT_DIR)

# 兼容层
import ultralytics
sys.modules['ultralytics.yolo'] = ultralytics
sys.modules['ultralytics.yolo.utils'] = ultralytics.utils
from ultralytics.utils import tal
sys.modules['ultralytics.yolo.utils.tal'] = tal

# 注入定制模块
spec = importlib.util.spec_from_file_location("cm", "ultralytics1/nn/modules.py")
cm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cm)
import ultralytics.nn.modules as m
for n in ['C2fNAM','NAMAttention','Channel_Att']: setattr(m, n, getattr(cm, n))
import ultralytics.nn as nn
for n in ['C2fNAM','NAMAttention','Channel_Att']: setattr(nn.modules, n, getattr(cm, n))

# 加载模型
from ultralytics import YOLO
import torch, onnx, shutil

model = YOLO("runs/segment/train12/weights/best.pt")
print("模型加载成功")

# C2fNAM pickle 反序列化时 __init__ 被跳过，_built 未设置
# m1 权重已从 checkpoint 加载，只补 _built
for mod in model.model.modules():
    if isinstance(mod, cm.C2fNAM) and not hasattr(mod, '_built'):
        mod._built = True

model.model.eval()
dummy = torch.randn(1, 3, 640, 640)
print("开始导出 ONNX...")
tmp_onnx = "best_tmp.onnx"
torch.onnx.export(
    model.model, dummy, tmp_onnx,
    opset_version=11,
    input_names=["images"],
    dynamo=False,
)

model_onnx = onnx.load(tmp_onnx)
print(f"\nONNX 输出节点名（ATC 要用这些名字）:")
for i, o in enumerate(model_onnx.graph.output):
    print(f"  [{i}] {o.name} shape={[d.dim_value for d in o.type.tensor_type.shape.dim]}")

shutil.copy(tmp_onnx, "best.onnx")
os.remove(tmp_onnx)
print(f"\n导出完成！best.onnx ({os.path.getsize('best.onnx') / 1024 / 1024:.1f} MB)")
