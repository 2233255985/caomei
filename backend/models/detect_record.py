import json
import os
from datetime import datetime
from extensions import db


class DetectRecord(db.Model):
    __tablename__ = 'detect_records'

    id = db.Column(db.Integer, primary_key=True)
    image_path = db.Column(db.String(500), nullable=False)
    result_json = db.Column(db.Text, nullable=True)
    count = db.Column(db.Integer, default=0)
    avg_confidence = db.Column(db.Float, default=0.0)
    annotated_path = db.Column(db.String(500), nullable=True)
    backend = db.Column(db.String(20), default='local')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        filename = os.path.basename(self.image_path)
        result = []
        if self.result_json:
            try:
                result = json.loads(self.result_json)
            except (json.JSONDecodeError, ValueError, TypeError):
                result = []
        d = {
            'id': self.id,
            'image_path': self.image_path,
            'image_url': f'/uploads/{filename}',
            'result_json': result,
            'count': self.count,
            'avg_confidence': round(self.avg_confidence, 4),
            'backend': self.backend,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
        if self.annotated_path:
            d['annotated_url'] = f'/annotated/{os.path.basename(self.annotated_path)}'
        return d
