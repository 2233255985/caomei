"""统计业务逻辑"""
from datetime import datetime, timedelta
from sqlalchemy import func
from models.detect_record import DetectRecord
from extensions import db


def get_summary():
    total = DetectRecord.query.count()
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = DetectRecord.query.filter(
        DetectRecord.created_at >= today_start
    ).count()

    avg_conf_row = db.session.query(func.avg(DetectRecord.avg_confidence)).scalar()
    avg_conf = round(float(avg_conf_row), 4) if avg_conf_row else 0.0

    total_strawberries = db.session.query(
        func.sum(DetectRecord.count)
    ).scalar() or 0

    return {
        'total_detections': total,
        'today_detections': today_count,
        'avg_confidence': avg_conf,
        'total_strawberries': int(total_strawberries),
    }


def get_trend(days=30):
    start_date = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.session.query(
            func.date(DetectRecord.created_at).label('date'),
            func.count(DetectRecord.id).label('detections'),
            func.sum(DetectRecord.count).label('strawberries'),
            func.avg(DetectRecord.avg_confidence).label('avg_conf'),
        )
        .filter(DetectRecord.created_at >= start_date)
        .group_by(func.date(DetectRecord.created_at))
        .order_by(func.date(DetectRecord.created_at))
        .all()
    )
    return [
        {
            'date': str(row.date),
            'detections': row.detections,
            'strawberries': int(row.strawberries) if row.strawberries else 0,
            'avg_confidence': round(float(row.avg_conf), 4) if row.avg_conf else 0.0,
        }
        for row in rows
    ]


def get_maturity_distribution():
    # 预留：当前仅有 1 类（Strawberry），后续可扩展成熟度分类
    return {'labels': [], 'values': [], 'placeholder': True}
