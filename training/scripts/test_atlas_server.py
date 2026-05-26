"""测试板子推理服务（绕过系统代理直连板子）"""
import requests, sys, os, glob

# 创建 session 并禁用代理（绕过 v2rayN 直连板子）
s = requests.Session()
s.trust_env = False

BASE = "http://192.168.1.2:6800"

# 找一张测试图
img_path = None
for p in [
    "C:/Users/tttjw/Desktop/code/atlas200/ultralytics-v8.0.45-relu6-tomato-seg/xilinx/vart_py/data/*.jpg",
    "C:/Users/tttjw/Desktop/code/atlas200/datasets/strawdi/val/images/*.jpg",
]:
    files = glob.glob(p)
    if files:
        img_path = files[0]
        break

if not img_path:
    print("找不到测试图片")
    sys.exit(1)

print(f"测试图片: {img_path}")

# 1. 测 health
print("\n=== 1. health ===")
try:
    r = s.get(f"{BASE}/health", timeout=5)
    print(f"  状态: {r.status_code}, 响应: {r.json()}")
except Exception as e:
    print(f"  X 连接失败: {e}")
    sys.exit(1)

# 2. 测 detect
print("\n=== 2. detect ===")
try:
    with open(img_path, "rb") as f:
        r = s.post(f"{BASE}/detect", files={"image": f}, timeout=30)
    print(f"  状态: {r.status_code}")
    data = r.json()
    dets = data.get("detections", [])
    print(f"  检测到 {len(dets)} 个草莓")
    for d in dets:
        print(f"    score={d['score']:.3f}  bbox={d['bbox']}")
except Exception as e:
    print(f"  X 检测失败: {e}")
    sys.exit(1)

print("\n全部通过")
