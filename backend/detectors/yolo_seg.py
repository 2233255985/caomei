"""YOLOv8-seg 推理引擎 — 从 test_onnx_windows.py 提取"""
import numpy as np
import cv2
import onnxruntime as ort


class YOLOv8SegEngine:
    def __init__(self, model_path, conf=0.25, iou=0.45, input_size=(640, 640)):
        self.session = ort.InferenceSession(model_path)
        self.input_name = self.session.get_inputs()[0].name
        self.input_size = input_size
        self.conf = conf
        self.iou = iou
        self.num_classes = 1  # 草莓只有 1 类

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
        cls = pred[:, 4:4 + self.num_classes]
        mc = pred[:, 4 + self.num_classes:]

        scores = cls.max(axis=1)
        cls_ids = cls.argmax(axis=1)
        valid = scores > self.conf

        if valid.sum() == 0:
            return []

        box = box[valid]
        scores = scores[valid]
        cls_ids = cls_ids[valid]
        mc = mc[valid]

        boxes_xyxy = np.zeros_like(box)
        boxes_xyxy[:, 0] = box[:, 0] - box[:, 2] / 2
        boxes_xyxy[:, 1] = box[:, 1] - box[:, 3] / 2
        boxes_xyxy[:, 2] = box[:, 0] + box[:, 2] / 2
        boxes_xyxy[:, 3] = box[:, 1] + box[:, 3] / 2

        boxes_xyxy[:, 0] = (boxes_xyxy[:, 0] - dw) / ratio
        boxes_xyxy[:, 1] = (boxes_xyxy[:, 1] - dh) / ratio
        boxes_xyxy[:, 2] = (boxes_xyxy[:, 2] - dw) / ratio
        boxes_xyxy[:, 3] = (boxes_xyxy[:, 3] - dh) / ratio

        h, w = self.orig_shape
        boxes_xyxy[:, 0] = np.clip(boxes_xyxy[:, 0], 0, w)
        boxes_xyxy[:, 1] = np.clip(boxes_xyxy[:, 1], 0, h)
        boxes_xyxy[:, 2] = np.clip(boxes_xyxy[:, 2], 0, w)
        boxes_xyxy[:, 3] = np.clip(boxes_xyxy[:, 3], 0, h)

        final_boxes, final_scores, final_cls = [], [], []
        for c in range(self.num_classes):
            mask_c = cls_ids == c
            if mask_c.sum() == 0:
                continue
            boxes_c = boxes_xyxy[mask_c]
            scores_c = scores[mask_c]
            keep = self.nms(boxes_c, scores_c, self.iou)
            final_boxes.append(boxes_c[keep])
            final_scores.append(scores_c[keep])
            final_cls.append(np.full(len(keep), c, dtype=np.int32))

        if not final_boxes:
            return []

        final_boxes = np.concatenate(final_boxes).tolist()
        final_scores = np.concatenate(final_scores).tolist()

        return [
            {'bbox': [int(b[0]), int(b[1]), int(b[2]), int(b[3])], 'score': round(s, 4)}
            for b, s in zip(final_boxes, final_scores)
        ]

    def inference(self, image):
        return self.session.run(None, {self.input_name: self.preprocess(image)})

    def detect(self, image):
        outputs = self.inference(image)
        return self.postprocess(outputs)
