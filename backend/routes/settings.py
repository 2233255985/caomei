import os
from flask import Blueprint, request, jsonify, current_app
from services.detect_service import get_backend, set_backend, get_detector, get_atlas_client, get_model_path, set_model_path

settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/backend', methods=['GET'])
def get_backend_setting():
    return jsonify({'backend': get_backend()})


@settings_bp.route('/backend', methods=['POST'])
def set_backend_setting():
    data = request.get_json()
    if not data or 'backend' not in data:
        return jsonify({'error': '请指定 backend (local/atlas)'}), 400
    backend = data['backend']
    if backend not in ('local', 'atlas'):
        return jsonify({'error': 'backend 必须是 local 或 atlas'}), 400
    set_backend(backend)
    return jsonify({'backend': backend, 'message': f'已切换到 {backend} 推理后端'})


@settings_bp.route('/model-path', methods=['GET'])
def get_model_path_setting():
    path = get_model_path(current_app)
    exists = os.path.exists(path) if path else False
    return jsonify({'model_path': path, 'exists': exists})


@settings_bp.route('/model-path', methods=['POST'])
def set_model_path_setting():
    data = request.get_json()
    if not data or 'model_path' not in data:
        return jsonify({'error': '请指定 model_path'}), 400
    path = data['model_path']
    exists = os.path.exists(path) if path else False
    set_model_path(path)
    msg = '模型路径已保存'
    if path and not exists:
        msg += '（警告：文件暂不存在）'
    return jsonify({'model_path': get_model_path(current_app), 'exists': exists, 'message': msg})
