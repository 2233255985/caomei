"""StrawDI PNG mask → YOLOv8 segmentation 格式转换"""
import os, cv2, numpy as np
from tqdm import tqdm

SRC = r"C:\Users\tttjw\Desktop\code\atlas200\StrawDI_Db1"
DST = r"C:\Users\tttjw\Desktop\code\atlas200\datasets\strawdi"
CLASS_NAME = "Strawberry"

def mask_to_yolo(mask_path, out_txt_path, img_w, img_h):
    """将 PNG instance mask 转为 YOLOv8 seg .txt（polygon 格式）"""
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
    if mask is None:
        return 0

    instance_ids = np.unique(mask)
    instance_ids = instance_ids[instance_ids > 0]  # 去掉背景 0
    count = 0

    with open(out_txt_path, 'w') as f:
        for inst_id in instance_ids:
            # 提取该实例的二值 mask
            binary = (mask == inst_id).astype(np.uint8) * 255
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                if len(cnt) < 3:
                    continue

                # 简化轮廓（epsilon=0.001 * 周长，约 200-500 点）
                epsilon = 0.001 * cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, epsilon, True)

                if len(approx) < 3:
                    continue

                # 归一化坐标
                line = ["0"]
                for pt in approx[:, 0]:
                    x = pt[0] / img_w
                    y = pt[1] / img_h
                    line.append(f"{x:.6f}")
                    line.append(f"{y:.6f}")

                f.write(" ".join(line) + "\n")
                count += 1

    return count


def convert_split(split_name):
    """转换一个 split（train/val/test）"""
    src_img_dir = os.path.join(SRC, split_name, "img")
    src_lbl_dir = os.path.join(SRC, split_name, "label")
    dst_img_dir = os.path.join(DST, split_name, "images")
    dst_lbl_dir = os.path.join(DST, split_name, "labels")
    os.makedirs(dst_img_dir, exist_ok=True)
    os.makedirs(dst_lbl_dir, exist_ok=True)

    files = sorted(os.listdir(src_img_dir))
    total_instances = 0

    for fname in tqdm(files, desc=f"Converting {split_name}"):
        if not fname.endswith('.png'):
            continue

        # 复制图片（重命名为 YOLO 风格文件名）
        stem = os.path.splitext(fname)[0]
        out_img = os.path.join(dst_img_dir, f"{stem}.jpg")
        out_txt = os.path.join(dst_lbl_dir, f"{stem}.txt")

        img = cv2.imread(os.path.join(src_img_dir, fname))
        if img is None:
            continue
        h, w = img.shape[:2]

        # 保存为 jpg
        cv2.imwrite(out_img, img, [cv2.IMWRITE_JPEG_QUALITY, 95])

        # 转换 mask → YOLO seg polygon
        n = mask_to_yolo(os.path.join(src_lbl_dir, fname), out_txt, w, h)
        total_instances += n

    print(f"  {split_name}: {len(files)} images, {total_instances} instances")


if __name__ == '__main__':
    print("Converting StrawDI_Db1 → YOLOv8 segmentation format...")
    for split in ['train', 'val', 'test']:
        convert_split(split)

    # 创建 data.yaml
    yaml_content = f"""names:
  - {CLASS_NAME}
nc: 1
train: ./train/images
val: ./val/images
"""
    with open(os.path.join(DST, "data.yaml"), 'w') as f:
        f.write(yaml_content)

    print(f"\nDone! Dataset saved to {DST}")
    print(f"data.yaml created with nc=1, class='{CLASS_NAME}'")
