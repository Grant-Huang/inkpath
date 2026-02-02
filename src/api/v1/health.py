"""健康检查API"""
from flask import Blueprint, jsonify

health_bp = Blueprint('health', __name__)


@health_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        'status': 'success',
        'message': 'InkPath API is running',
        'version': '0.1.0'
    }), 200
