"""Atlas 200 DK 远程推理客户端"""
import os
import requests


class AtlasClient:
    def __init__(self, base_url='http://192.168.1.2:6800'):
        self.base_url = base_url.rstrip('/')
        self._session = requests.Session()
        self._session.trust_env = False  # 绕过系统代理（v2rayN）

    def detect(self, image_path):
        normalized = os.path.normpath(image_path)
        if not os.path.exists(normalized):
            raise FileNotFoundError(f'文件不存在: {image_path}')
        with open(normalized, 'rb') as f:
            resp = self._session.post(
                f'{self.base_url}/detect', files={'image': f}, timeout=30
            )
        resp.raise_for_status()
        data = resp.json()
        if 'error' in data:
            raise RuntimeError(f'板子返回错误: {data["error"]}')
        return data.get('detections', [])

    def is_available(self):
        try:
            resp = self._session.get(f'{self.base_url}/health', timeout=5)
            return resp.status_code == 200
        except requests.RequestException:
            return False
