"""Atlas 200 DK ACLLite 推理服务 — JSON API"""
import os, sys, time, traceback
import numpy as np
import cv2
from flask import Flask, request, jsonify
from flask_cors import CORS

# ACLLite
ACLLITE_PATH = "/home/HwHiAiUser/Ascend/thirdpart/aarch64/acllite"
sys.path.append(ACLLITE_PATH)
from acllite_model import AclLiteModel
from acllite_resource import AclLiteResource

# 复用 yolo_acllite.py 的 YOLOv8Seg 类
sys.path.insert(0, "/home/HwHiAiUser")
from yolo_acllite import YOLOv8Seg

app = Flask(__name__)
CORS(app)
detector = None


@app.route("/health")
def health():
    return jsonify({"status": "ok", "model_loaded": detector is not None})


@app.route("/detect", methods=["POST"])
def detect():
    if "image" not in request.files:
        return jsonify({"error": "No image file"}), 400

    file = request.files["image"]
    file_bytes = np.frombuffer(file.read(), np.uint8)
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    if image is None:
        return jsonify({"error": "Failed to decode image"}), 400

    try:
        t0 = time.time()
        outputs = detector.inference(image)
        detections = detector.postprocess(outputs)
        t1 = time.time()
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Inference failed: {str(e)}"}), 500

    results = []
    for box, score, cls_id, _ in detections:
        results.append({
            "bbox": [int(box[0]), int(box[1]), int(box[2]), int(box[3])],
            "score": round(float(score), 4),
        })

    elapsed = int((t1 - t0) * 1000)
    print(f"  detect {len(results)} objects, {elapsed}ms")
    return jsonify({"detections": results, "elapsed_ms": elapsed})


if __name__ == "__main__":
    model_path = "/home/HwHiAiUser/best.om"
    classes_path = "/home/HwHiAiUser/model_data/classes.txt"
    detector = YOLOv8Seg(model_path, classes_path)
    print(f"模型加载成功，监听 0.0.0.0:6800")
    app.run(host="0.0.0.0", port=6800, debug=False)
