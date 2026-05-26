"""视频逐帧检测服务"""
import os
import time
import uuid
import subprocess
import cv2
from services.annotate import draw_bboxes

# FFmpeg 路径（winget 安装位置）
_FFMPEG_PATH = r"C:\Users\tttjw\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-full_build\bin\ffmpeg.exe"


def _transcode_to_h264(input_path, output_path):
    """用 FFmpeg 将 mp4v 转码为浏览器可播放的 H.264"""
    try:
        subprocess.run(
            [_FFMPEG_PATH, '-y', '-i', input_path,
             '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
             '-pix_fmt', 'yuv420p',
             output_path],
            capture_output=True, timeout=600, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return False


def process_video(video_path, detect_func, output_dir, fps_target=30, progress_callback=None):
    """逐帧检测视频，返回标注视频路径和统计信息"""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError('无法打开视频文件')

    orig_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # 计算帧采样间隔
    if orig_fps > fps_target:
        step = int(round(orig_fps / fps_target))
    else:
        step = 1
        fps_target = orig_fps

    estimated_processed = max(total_frames // step, 1) if step > 0 else 1

    # 准备输出视频
    out_filename = f"result_{uuid.uuid4().hex}.mp4"
    out_path = os.path.join(output_dir, out_filename)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(out_path, fourcc, fps_target, (width, height))

    frame_idx = 0
    processed = 0
    total_detections = 0
    t0 = time.time()

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frame_idx += 1

            if (frame_idx - 1) % step != 0:
                continue

            processed += 1
            detections = detect_func(frame)
            total_detections += len(detections)
            annotated = draw_bboxes(frame, detections)
            writer.write(annotated)
            if progress_callback:
                progress_callback(processed, estimated_processed)
    finally:
        cap.release()
        writer.release()

    # 转码为 H.264 以便浏览器播放
    h264_path = out_path.replace('.mp4', '_h264.mp4')
    if _transcode_to_h264(out_path, h264_path):
        os.replace(h264_path, out_path)

    elapsed = time.time() - t0

    return {
        'video_url': f'/videos/{out_filename}',
        'total_frames': total_frames,
        'processed_frames': processed,
        'total_detections': total_detections,
        'avg_per_frame': round(total_detections / max(processed, 1), 2),
        'elapsed_seconds': round(elapsed, 1),
        'fps_processed': round(processed / max(elapsed, 0.01), 1),
    }
