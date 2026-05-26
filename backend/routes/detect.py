from flask import Blueprint, request, jsonify, current_app
from services.detect_service import run_detect, get_history, get_record, delete_record
from services import detect_service

detect_bp = Blueprint('detect', __name__)


@detect_bp.route('', methods=['POST'])
def detect():
    if 'image' not in request.files:
        return jsonify({'error': '请上传图片'}), 400
    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({'error': '请选择图片'}), 400

    try:
        result = run_detect(image_file, current_app)
        return jsonify(result), 200
    except RuntimeError as e:
        return jsonify({'error': str(e)}), 503
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'检测失败: {str(e)}'}), 500


@detect_bp.route('/history', methods=['GET'])
def history():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    return jsonify(get_history(page=page, per_page=per_page))


@detect_bp.route('/history/<int:record_id>', methods=['GET'])
def detail(record_id):
    record = get_record(record_id)
    if record:
        return jsonify(record)
    return jsonify({'error': '记录不存在'}), 404


@detect_bp.route('/history/<int:record_id>', methods=['DELETE'])
def delete(record_id):
    if delete_record(record_id):
        return jsonify({'message': '删除成功'})
    return jsonify({'error': '记录不存在'}), 404


@detect_bp.route('/video', methods=['POST'])
def detect_video():
    if 'video' not in request.files:
        return jsonify({'error': '请上传视频'}), 400
    video_file = request.files['video']
    if video_file.filename == '':
        return jsonify({'error': '请选择视频'}), 400

    try:
        # 解析 current_app 代理为真实对象再传入（后台线程需要）
        app = current_app._get_current_object()
        task_id = detect_service.video_detect(video_file, app)
        return jsonify({'task_id': task_id}), 202
    except RuntimeError as e:
        return jsonify({'error': str(e)}), 503
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'视频检测失败: {str(e)}'}), 500


@detect_bp.route('/video/progress/<task_id>', methods=['GET'])
def video_progress(task_id):
    task = detect_service.get_video_progress(task_id)
    if not task:
        return jsonify({'error': '任务不存在'}), 404
    return jsonify(task)


@detect_bp.route('/batch', methods=['POST'])
def detect_batch():
    files = request.files.getlist('images')
    if not files:
        return jsonify({'error': '请上传图片'}), 400

    max_files = current_app.config.get('BATCH_MAX_FILES', 100)
    if len(files) > max_files:
        return jsonify({'error': f'单次最多 {max_files} 张图片'}), 400

    try:
        result = detect_service.batch_detect(files, current_app)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': f'批量检测失败: {str(e)}'}), 500
