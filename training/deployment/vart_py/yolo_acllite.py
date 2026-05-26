"""Atlas 200 DK YOLOv8-seg 推理 — 图片模式"""
import os, sys, time, colorsys, random
import numpy as np
import cv2

ACLLITE_PATH = "/home/HwHiAiUser/Ascend/thirdpart/aarch64/acllite"
sys.path.append(ACLLITE_PATH)
from acllite_model import AclLiteModel
from acllite_resource import AclLiteResource


class YOLOv8Seg:
    def __init__(self, model_path, classes_path, conf=0.25, iou=0.45, input_size=(640, 640)):
        self.acl = AclLiteResource()
        self.acl.init()
        self.model = AclLiteModel(model_path)
        self.input_size = input_size
        self.conf = conf
        self.iou = iou
        self.num_masks = 32

        with open(classes_path) as f:
            self.class_names = [c.strip() for c in f.readlines()]
        self.num_classes = len(self.class_names)

        # 颜色
        hsv = [(1.0 * x / self.num_classes, 1., 1.) for x in range(self.num_classes)]
        self.colors = [tuple(int(c * 255) for c in colorsys.hsv_to_rgb(*h)) for h in hsv]
        random.seed(0); random.shuffle(self.colors); random.seed(None)

    def letterbox(self, im, color=(114, 114, 114)):
        shape = im.shape[:2]
        r = min(self.input_size[0] / shape[0], self.input_size[1] / shape[1])
        nu = int(round(shape[1] * r)), int(round(shape[0] * r))
        dw, dh = self.input_size[1] - nu[0], self.input_size[0] - nu[1]
        dw /= 2; dh /= 2
        if shape[::-1] != nu:
            im = cv2.resize(im, nu, interpolation=cv2.INTER_LINEAR)
        im = cv2.copyMakeBorder(im, int(round(dh - 0.1)), int(round(dh + 0.1)),
                                int(round(dw - 0.1)), int(round(dw + 0.1)),
                                cv2.BORDER_CONSTANT, value=color)
        self._pad = (dw, dh, r)
        return im

    def preprocess(self, image):
        self.orig_shape = image.shape[:2]
        padded = self.letterbox(image)
        img = cv2.cvtColor(padded, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        return np.ascontiguousarray(np.transpose(img, (2, 0, 1))[np.newaxis, ...])

    def nms(self, boxes, scores, iou_thresh):
        """NMS: boxes (N,4) xyxy, scores (N,)"""
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

        # output[0]: (1, 4+nc+32, 8400) — concat 检测输出
        pred = outputs[0][0]
        pred = np.transpose(pred, (1, 0))

        box = pred[:, :4]        # xywh
        cls = pred[:, 4:4 + self.num_classes]    # 各类别分数
        mc = pred[:, 4 + self.num_classes:]      # mask 系数 (32 维)

        # 获取最高分和类别
        scores = cls.max(axis=1)
        cls_ids = cls.argmax(axis=1)
        valid = scores > self.conf

        if valid.sum() == 0:
            return [], []

        box = box[valid]
        scores = scores[valid]
        cls_ids = cls_ids[valid]
        mc = mc[valid]

        # xywh -> xyxy
        boxes_xyxy = np.zeros_like(box)
        boxes_xyxy[:, 0] = box[:, 0] - box[:, 2] / 2
        boxes_xyxy[:, 1] = box[:, 1] - box[:, 3] / 2
        boxes_xyxy[:, 2] = box[:, 0] + box[:, 2] / 2
        boxes_xyxy[:, 3] = box[:, 1] + box[:, 3] / 2

        # 还原到原图坐标
        boxes_xyxy[:, 0] = (boxes_xyxy[:, 0] - dw) / ratio
        boxes_xyxy[:, 1] = (boxes_xyxy[:, 1] - dh) / ratio
        boxes_xyxy[:, 2] = (boxes_xyxy[:, 2] - dw) / ratio
        boxes_xyxy[:, 3] = (boxes_xyxy[:, 3] - dh) / ratio

        # 限制在图像边界
        h, w = self.orig_shape
        boxes_xyxy[:, 0] = np.clip(boxes_xyxy[:, 0], 0, w)
        boxes_xyxy[:, 1] = np.clip(boxes_xyxy[:, 1], 0, h)
        boxes_xyxy[:, 2] = np.clip(boxes_xyxy[:, 2], 0, w)
        boxes_xyxy[:, 3] = np.clip(boxes_xyxy[:, 3], 0, h)

        # NMS（按类别分别 NMS）
        final_boxes, final_scores, final_cls, final_mc = [], [], [], []
        for c in range(self.num_classes):
            mask_c = cls_ids == c
            if mask_c.sum() == 0:
                continue
            boxes_c = boxes_xyxy[mask_c]
            scores_c = scores[mask_c]
            mc_c = mc[mask_c]
            keep = self.nms(boxes_c, scores_c, self.iou)
            final_boxes.append(boxes_c[keep])
            final_scores.append(scores_c[keep])
            final_cls.append(np.full(len(keep), c, dtype=np.int32))
            final_mc.append(mc_c[keep])

        if not final_boxes:
            return [], []

        final_boxes = np.concatenate(final_boxes)
        final_scores = np.concatenate(final_scores)
        final_cls = np.concatenate(final_cls)
        final_mc = np.concatenate(final_mc)

        # 生成 mask（使用 prototype masks: output[5]）
        protos = outputs[5][0]                    # (32, 160, 160)
        masks = np.dot(final_mc, protos.reshape(32, -1))  # (N, 25600)
        masks = 1 / (1 + np.exp(-masks))          # sigmoid
        masks = masks.reshape(-1, 160, 160)

        # resize mask 到原图
        result_masks = []
        for i in range(len(final_boxes)):
            m = cv2.resize(masks[i], (w, h), interpolation=cv2.INTER_LINEAR)
            # 用 box 裁剪 mask
            x1, y1, x2, y2 = final_boxes[i].astype(int)
            m[:y1, :] = 0; m[y2:, :] = 0
            m[:, :x1] = 0; m[:, x2:] = 0
            result_masks.append(m > 0.5)

        return list(zip(final_boxes, final_scores, final_cls, result_masks))

    def inference(self, image):
        return self.model.execute([self.preprocess(image)])

    def draw(self, image, detections, show_mask=False):
        out = image.copy()
        for box, score, cls_id, mask in detections:
            x1, y1, x2, y2 = box.astype(int)
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(out.shape[1]-1, x2), min(out.shape[0]-1, y2)
            color = self.colors[cls_id]
            label = f"{self.class_names[cls_id]} {score:.2f}"

            # mask（半透明覆盖）
            if show_mask and mask is not None and mask.any():
                colored = np.zeros_like(out)
                colored[:, :, 0] = mask * color[0]
                colored[:, :, 1] = mask * color[1]
                colored[:, :, 2] = mask * color[2]
                out = cv2.addWeighted(out, 0.6, colored, 0.4, 0)

            # box
            cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)

            # label
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(out, (x1, max(0, y1 - th - 6)), (min(x1 + tw, out.shape[1]-1), y1), color, -1)
            cv2.putText(out, label, (x1, max(0, y1 - 4)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        return out


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    model_path = "/home/HwHiAiUser/best.om"
    classes_path = "model_data/classes.txt"
    detector = YOLOv8Seg(model_path, classes_path)
    print(f"模型加载成功，{detector.model._output_size} 个输出")

    # 处理 data 目录下的所有图片
    data_dir = "data"
    if not os.path.exists(data_dir):
        print(f"data 目录不存在，创建后把测试图放进去")
        os.makedirs(data_dir, exist_ok=True)
        return

    out_dir = "out"
    os.makedirs(out_dir, exist_ok=True)

    for fname in sorted(os.listdir(data_dir)):
        if not fname.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue
        path = os.path.join(data_dir, fname)
        img = cv2.imread(path)
        if img is None:
            print(f"  无法读取: {fname}")
            continue
        print(f"\n处理: {fname} ({img.shape[1]}x{img.shape[0]}, min={img.min()} max={img.max()} mean={img.mean():.1f})")

        t0 = time.time()
        outputs = detector.inference(img)
        t1 = time.time()
        detections = detector.postprocess(outputs)
        t2 = time.time()

        print(f"  检测到 {len(detections)} 个目标, 推理:{(t1-t0)*1000:.0f}ms, 后处理:{(t2-t1)*1000:.0f}ms")
        for box, score, cls_id, _ in detections:
            print(f"  {detector.class_names[cls_id]} {score:.2f} ({int(box[0])},{int(box[1])})-({int(box[2])},{int(box[3])})")

        # debug: 先保存一张原图对比
        cv2.imwrite(os.path.join(out_dir, "debug_" + fname), img)
        print(f"  原图已保存: debug_{fname}")

        result = detector.draw(img, detections, show_mask=False)
        out_path = os.path.join(out_dir, fname)
        cv2.imwrite(out_path, result)
        print(f"  保存: {out_path}")


if __name__ == "__main__":
    main()
