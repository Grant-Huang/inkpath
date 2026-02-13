"""配置管理 API"""
from flask import Blueprint, jsonify
from src.config import Config

config_bp = Blueprint('config', __name__)


@config_bp.route('/config', methods=['GET'])
def get_config():
    """获取前端可用的配置"""
    return jsonify({
        'status': 'success',
        'data': {
            'summary_trigger_count': getattr(Config, 'SUMMARY_TRIGGER_COUNT', 5),
            'coherence_check_enabled': Config.ENABLE_COHERENCE_CHECK,
        }
    }), 200
