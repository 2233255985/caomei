"""检测业务逻辑"""
import os
import json
import uuid
import cv2
import threading
from datetime import datetime
from extensions import db
from models.detect_record import DetectRecord
from detectors.local_detector import LocalDetector
from detectors.atlas_client import AtlasClient
from services.annotate import draw_bboxes

# 全局单例
_detector = None
_atlas_client = None
_current_backend = 'local'
_custom_model_path = None
_CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config_settings.json')
_video_tasks = {}
_tasks_lock = threading.Lock()


def _load_settings():
    if os.path.exists(_CONFIG_FILE):
        try:
            with open(_CONFIG_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def _save_settings(updates):
    settings = _load_settings()
    settings.update(updates)
    with open(_CONFIG_FILE, 'w') as f:
        json.dump(settings, f, indent=2)


def get_model_path(app):
    global _custom_model_path
    if _custom_model_path is None:
        settings = _load_settings()
        _custom_model_path = settings.get('model_path', app.config['MODEL_PATH'])
    return _custom_model_path


def set_model_path(path):
    global _custom_model_path, _detector
    path = os.path.abspath(path) if path else None
    _custom_model_path = path
    _detector = None  # 重置检测器，下次检测时重新加载
    if path:
        _save_settings({'model_path': path})
    else:
        _save_settings({'model_path': None})


def get_backend():
    return _current_backend


def set_backend(backend):
    global _current_backend
    if backend in ('local', 'atlas'):
        _current_backend = backend


def get_detector(app):
    global _detector
    if _detector is None:
        _detector = LocalDetector(get_model_path(app))
    return _detector


def get_atlas_client(app):
    global _atlas_client
    if _atlas_client is None:
        _atlas_client = AtlasClient(app.config['ATLAS_URL'])
    return _atlas_client


def run_detect(image_file, app):
    # 保存上传的图片
    upload_dir = app.config['UPLOAD_FOLDER']
    ext = os.path.splitext(image_file.filename)[1] or '.jpg'
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(upload_dir, filename)
    image_file.save(filepath)

    # 执行检测
    if _current_backend == 'local':
        detector = get_detector(app)
        if not detector.is_available():
            raise RuntimeError('本地模型不可用，请检查模型路径或切换到 Atlas 后端')
        detections = detector.detect(filepath)
    else:
        client = get_atlas_client(app)
        detections = client.detect(filepath)

    # 生成标注图
    annotated_path = None
    annotated_filename = None
    if detections:
        img = cv2.imread(filepath)
        if img is not None:
            annotated_filename = f"annotated_{filename}"
            annotated_path = os.path.join(app.config['ANNOTATED_FOLDER'], annotated_filename)
            draw_bboxes(img, detections, output_path=annotated_path)

    # 统计
    count = len(detections)
    avg_conf = sum(d['score'] for d in detections) / count if count > 0 else 0.0

    # 保存记录
    record = DetectRecord(
        image_path=filepath,
        result_json=json.dumps(detections),
        count=count,
        avg_confidence=avg_conf,
        backend=_current_backend,
        annotated_path=annotated_path,
        created_at=datetime.utcnow(),
    )
    db.session.add(record)
    db.session.commit()

    result = {
        'id': record.id,
        'detections': detections,
        'count': count,
        'avg_confidence': round(avg_conf, 4),
        'image_url': f'/uploads/{filename}',
        'backend': _current_backend,
    }
    if annotated_path:
        result['annotated_url'] = f'/annotated/{annotated_filename}'
    return result


def get_history(page=1, per_page=20):
    pagination = DetectRecord.query.order_by(
        DetectRecord.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    return {
        'items': [r.to_dict() for r in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'per_page': pagination.per_page,
    }


def get_record(record_id):
    record = DetectRecord.query.get(record_id)
    return record.to_dict() if record else None


def delete_record(record_id):
    record = DetectRecord.query.get(record_id)
    if record:
        if os.path.exists(record.image_path):
            os.remove(record.image_path)
        db.session.delete(record)
        db.session.commit()
        return True
    return False


def _make_atlas_detect_func(app):
    """创建 Atlas 后端的帧检测函数"""
    client = AtlasClient(app.config['ATLAS_URL'])
    def detect_func(frame):
        _, buf = cv2.imencode('.jpg', frame)
        temp_path = os.path.join(app.config['VIDEO_FOLDER'], f"_frame_{uuid.uuid4().hex}.jpg")
        with open(temp_path, 'wb') as f:
            f.write(buf.tobytes())
        try:
            return client.detect(temp_path)
        finally:
            os.remove(temp_path)
    return detect_func


def video_detect(video_file, app):
    """启动异步视频检测，返回 task_id"""
    upload_dir = app.config['VIDEO_FOLDER']
    ext = os.path.splitext(video_file.filename)[1] or '.mp4'
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(upload_dir, filename)
    video_file.save(filepath)

    task_id = uuid.uuid4().hex
    with _tasks_lock:
        _video_tasks[task_id] = {'progress': 0, 'status': 'processing', 'result': None, 'error': None}

    def _progress(processed, total):
        pct = int(processed / max(total, 1) * 100)
        with _tasks_lock:
            if task_id in _video_tasks:
                _video_tasks[task_id]['progress'] = pct

    def _run(app_obj):
        try:
            if _current_backend == 'local':
                detector = get_detector(app_obj)
                if not detector.is_available():
                    raise RuntimeError('本地模型不可用')
                def detect_func(frame):
                    return detector.detect(frame)
            else:
                detect_func = _make_atlas_detect_func(app_obj)

            from services.video_processor import process_video
            result = process_video(filepath, detect_func, upload_dir, progress_callback=_progress)

            with _tasks_lock:
                _video_tasks[task_id]['status'] = 'done'
                _video_tasks[task_id]['progress'] = 100
                _video_tasks[task_id]['result'] = result
        except Exception as e:
            with _tasks_lock:
                _video_tasks[task_id]['status'] = 'error'
                _video_tasks[task_id]['error'] = str(e)

    thread = threading.Thread(target=_run, args=(app,), daemon=True)
    thread.start()
    return task_id


def get_video_progress(task_id):
    with _tasks_lock:
        return _video_tasks.get(task_id)


def batch_detect(image_files, app):
    results = []
    for img_file in image_files:
        try:
            result = run_detect(img_file, app)
            results.append({
                'filename': img_file.filename,
                'count': result['count'],
                'avg_confidence': result['avg_confidence'],
                'detections': result['detections'],
                'image_url': result['image_url'],
                'annotated_url': result.get('annotated_url'),
            })
        except Exception as e:
            results.append({
                'filename': img_file.filename,
                'error': str(e),
                'count': 0,
            })

    return {'results': results, 'total': len(results), 'success': sum(1 for r in results if r['count'] > 0)}
