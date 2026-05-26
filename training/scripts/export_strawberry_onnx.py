"""导出草莓 ONNX（nc=1, opset=11）"""
import sys, os, importlib.util

PROJECT_DIR = r"C:\Users\tttjw\Desktop\code\atlas200\ultralytics-v8.0.45-relu6-tomato-seg"
os.chdir(PROJECT_DIR)

# 兼容层
import ultralytics
sys.modules['ultralytics.yolo'] = ultralytics
sys.modules['ultralytics.yolo.utils'] = ultralytics.utils
from ultralytics.utils import tal
sys.modules['ultralytics.yolo.utils.tal'] = tal

# 注入定制模块（checkpoint 含 C2fNAM 引用）
spec = importlib.util.spec_from_file_location("cm", "ultralytics1/nn/modules.py")
cm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cm)
import ultralytics.nn.modules as m
for n in ['C2fNAM','NAMAttention','Channel_Att']: setattr(m, n, getattr(cm, n))
import ultralytics.nn as nn
for n in ['C2fNAM','NAMAttention','Channel_Att']: setattr(nn.modules, n, getattr(cm, n))

from ultralytics import YOLO
import torch, onnx, shutil

model = YOLO("runs/segment/strawberry-v2/weights/best.pt")
print("模型加载成功")

model.model.eval()
dummy = torch.randn(1, 3, 640, 640)
print("开始导出 ONNX（opset=11, dynamo=False）...")
tmp_onnx = "best_strawberry_tmp.onnx"
torch.onnx.export(
    model.model, dummy, tmp_onnx,
    opset_version=11,
    input_names=["images"],
    dynamo=False,
)

# 打印输出节点名
model_onnx = onnx.load(tmp_onnx)
print(f"\nONNX 输出节点名:")
for i, o in enumerate(model_onnx.graph.output):
    print(f"  [{i}] {o.name} shape={[d.dim_value for d in o.type.tensor_type.shape.dim]}")

# 复制到项目根目录
shutil.copy(tmp_onnx, "best.onnx")
os.remove(tmp_onnx)
print(f"\n导出完成: best.onnx ({os.path.getsize('best.onnx')/1024/1024:.1f} MB)")
