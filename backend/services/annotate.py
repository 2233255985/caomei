"""标注图画框工具"""
import cv2
import numpy as np


def draw_bboxes(image, detections, output_path=None, label="Strawberry"):
    """在图像上画检测框，可选保存到文件"""
    img = image.copy()
    if not detections:
        return img

    colors = [(0, 0, 255), (67, 160, 71), (30, 136, 229), (251, 140, 0), (142, 36, 170),
              (121, 85, 72), (0, 150, 136), (63, 81, 181), (233, 30, 99), (255, 152, 0)]

    for i, d in enumerate(detections):
        x1, y1, x2, y2 = map(int, d['bbox'])
        score = d['score']
        color = colors[i % len(colors)]
        text = f"{label} {score:.1%}"

        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
        cv2.rectangle(img, (x1, y1 - th - 6), (x1 + tw, y1), color, -1)
        cv2.putText(img, text, (x1, y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

    if output_path:
        cv2.imwrite(output_path, img)
    return img
