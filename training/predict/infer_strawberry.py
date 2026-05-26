"""草莓分割推理 (nc=1) — ONNX Runtime"""
import os, sys, time
import numpy as np
import cv2
import onnxruntime as ort

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

CLASSES = ["Strawberry"]
NUM_CLASSES = 1
NUM_MASKS = 32

COLORS = [(0, 255, 0)]


class YOLOv8Seg:
    def __init__(self, model_path, conf=0.25, iou=0.45, input_size=(640, 640)):
        self.session = ort.InferenceSession(model_path)
        self.input_name = self.session.get_inputs()[0].name
        self.input_size = input_size
        self.conf = conf
        self.iou = iou

    def letterbox(self, im, color=(114, 114, 114)):
        shape = im.shape[:2]
        r = min(self.input_size[0] / shape[0], self.input_size[1] / shape[1])
        nu = int(round(shape[1] * r)), int(round(shape[0] * r))
        dw, dh = self.input_size[1] - nu[0], self.input_size[0] - nu[1]
        dw /= 2
        dh /= 2
        if shape[::-1] != nu:
            im = cv2.resize(im, nu, interpolation=cv2.INTER_LINEAR)
        im = cv2.copyMakeBorder(
            im, int(round(dh - 0.1)), int(round(dh + 0.1)),
            int(round(dw - 0.1)), int(round(dw + 0.1)),
            cv2.BORDER_CONSTANT, value=color,
        )
        self._pad = (dw, dh, r)
        return im

    def preprocess(self, image):
        self.orig_shape = image.shape[:2]
        padded = self.letterbox(image)
        img = cv2.cvtColor(padded, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        return np.ascontiguousarray(np.transpose(img, (2, 0, 1))[np.newaxis, ...])

    def nms(self, boxes, scores, iou_thresh):
        x1, y1, x2, y2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
        areas = (x2 - x1 + 1e-9) * (y2 - y1 + 1e-9)
        order = scores.argsort()[::-1]
        keep = []
        while order.size > 0:
            i = order[0]
            keep.append(i)
            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])
            w = np.maximum(0.0, xx2 - xx1)
            h = np.maximum(0.0, yy2 - yy1)
            inter = w * h
            ovr = inter / (areas[i] + areas[order[1:]] - inter)
            inds = np.where(ovr <= iou_thresh)[0]
            order = order[inds + 1]
        return keep

    def postprocess(self, outputs):
        dw, dh, ratio = self._pad
        pred = outputs[0][0]
        pred = np.transpose(pred, (1, 0))

        box = pred[:, :4]
        cls = pred[:, 4:4 + NUM_CLASSES]
        mc = pred[:, 4 + NUM_CLASSES:]

        scores = cls.max(axis=1)
        cls_ids = cls.argmax(axis=1)
        valid = scores > self.conf

        if valid.sum() == 0:
            return []

        box, scores, cls_ids, mc = box[valid], scores[valid], cls_ids[valid], mc[valid]

        boxes_xyxy = np.zeros_like(box)
        boxes_xyxy[:, 0] = box[:, 0] - box[:, 2] / 2
        boxes_xyxy[:, 1] = box[:, 1] - box[:, 3] / 2
        boxes_xyxy[:, 2] = box[:, 0] + box[:, 2] / 2
        boxes_xyxy[:, 3] = box[:, 1] + box[:, 3] / 2

        for j in range(4):
            boxes_xyxy[:, j] = (boxes_xyxy[:, j] - (dw if j % 2 == 0 else dh)) / ratio

        h, w = self.orig_shape
        boxes_xyxy[:, 0] = np.clip(boxes_xyxy[:, 0], 0, w)
        boxes_xyxy[:, 1] = np.clip(boxes_xyxy[:, 1], 0, h)
        boxes_xyxy[:, 2] = np.clip(boxes_xyxy[:, 2], 0, w)
        boxes_xyxy[:, 3] = np.clip(boxes_xyxy[:, 3], 0, h)

        final_boxes, final_scores, final_cls, final_mc = [], [], [], []
        for c in range(NUM_CLASSES):
            mask_c = cls_ids == c
            if mask_c.sum() == 0:
                continue
            keep = self.nms(boxes_xyxy[mask_c], scores[mask_c], self.iou)
            final_boxes.append(boxes_xyxy[mask_c][keep])
            final_scores.append(scores[mask_c][keep])
            final_cls.append(np.full(len(keep), c, dtype=np.int32))
            final_mc.append(mc[mask_c][keep])

        if not final_boxes:
            return []

        final_boxes = np.concatenate(final_boxes)
        final_scores = np.concatenate(final_scores)
        final_cls = np.concatenate(final_cls)
        final_mc = np.concatenate(final_mc)

        protos = outputs[5][0]
        masks = np.dot(final_mc, protos.reshape(NUM_MASKS, -1))
        masks = 1 / (1 + np.exp(-masks))
        masks = masks.reshape(-1, 160, 160)

        result_masks = []
        for i in range(len(final_boxes)):
            m = cv2.resize(masks[i], (w, h), interpolation=cv2.INTER_LINEAR)
            x1, y1, x2, y2 = final_boxes[i].astype(int)
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)
            mask_crop = np.zeros((h, w), dtype=np.uint8)
            mask_crop[y1:y2, x1:x2] = (m[y1:y2, x1:x2] > 0.5).astype(np.uint8)
            result_masks.append(mask_crop.astype(bool))

        return list(zip(final_boxes, final_scores, final_cls, result_masks))

    def inference(self, image):
        return self.session.run(None, {self.input_name: self.preprocess(image)})

    def draw(self, image, detections, show_mask=False):
        out = image.copy()
        # 累积所有 mask 到 overlay，只 blend 一次
        if show_mask and detections:
            overlay = np.zeros_like(image, dtype=np.float32)
            for _, _, cls_id, mask in detections:
                if mask is not None and mask.any():
                    for c in range(3):
                        overlay[:, :, c] += mask * COLORS[cls_id][c]
            overlay = np.clip(overlay, 0, 255).astype(np.uint8)
            out = cv2.addWeighted(out, 0.6, overlay, 0.4, 0)

        for box, score, cls_id, _ in detections:
            x1, y1, x2, y2 = box.astype(int)
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(out.shape[1] - 1, x2), min(out.shape[0] - 1, y2)
            color = COLORS[cls_id]
            label = f"{CLASSES[cls_id]} {score:.2f}"

            cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(out, (x1, max(0, y1 - th - 6)),
                          (min(x1 + tw, out.shape[1] - 1), y1), color, -1)
            cv2.putText(out, label, (x1, max(0, y1 - 4)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        return out


def main():
    model_path = os.path.join(SCRIPT_DIR, "strawberry.onnx")
    if not os.path.exists(model_path):
        print(f"[错误] 模型文件不存在: {model_path}")
        return

    detector = YOLOv8Seg(model_path)
    print(f"草莓模型加载成功")

    data_dir = os.path.join(SCRIPT_DIR, "data")
    out_dir = os.path.join(SCRIPT_DIR, "out")
    os.makedirs(out_dir, exist_ok=True)

    if not os.path.isdir(data_dir):
        print(f"创建 {data_dir} 目录并把测试图片放进去")
        os.makedirs(data_dir, exist_ok=True)
        return

    for fname in sorted(os.listdir(data_dir)):
        if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
            continue
        path = os.path.join(data_dir, fname)
        img = cv2.imread(path)
        if img is None:
            print(f"  无法读取: {fname}")
            continue
        print(f"\n处理: {fname} ({img.shape[1]}x{img.shape[0]})")

        t0 = time.time()
        outputs = detector.inference(img)
        t1 = time.time()
        detections = detector.postprocess(outputs)
        t2 = time.time()

        print(f"  检测到 {len(detections)} 个, 推理:{(t1 - t0) * 1000:.0f}ms, 后处理:{(t2 - t1) * 1000:.0f}ms")
        for box, score, cls_id, _ in detections:
            print(f"  {CLASSES[cls_id]} {score:.2f} ({int(box[0])},{int(box[1])})-({int(box[2])},{int(box[3])})")

        result = detector.draw(img, detections, show_mask=False)
        out_path = os.path.join(out_dir, fname)
        cv2.imwrite(out_path, result)
        print(f"  保存: {out_path}")


if __name__ == "__main__":
    main()
