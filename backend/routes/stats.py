from flask import Blueprint, request, jsonify
from services.stats_service import get_summary, get_trend, get_maturity_distribution

stats_bp = Blueprint('stats', __name__)


@stats_bp.route('/summary', methods=['GET'])
def summary():
    return jsonify(get_summary())


@stats_bp.route('/trend', methods=['GET'])
def trend():
    days = request.args.get('days', 30, type=int)
    return jsonify(get_trend(days=days))


@stats_bp.route('/maturity', methods=['GET'])
def maturity():
    return jsonify(get_maturity_distribution())
