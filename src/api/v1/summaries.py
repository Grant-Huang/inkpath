"""摘要API"""
from flask import Blueprint, request, jsonify, current_app
from sqlalchemy.orm import Session
import uuid
from src.database import get_db
from src.services.summary_service import get_branch_summary, generate_summary


def get_db_session():
    """获取数据库会话（支持测试模式）"""
    if current_app.config.get('TESTING') and 'TEST_DB' in current_app.config:
        return current_app.config['TEST_DB']
    return next(get_db())


summaries_bp = Blueprint('summaries', __name__)


@summaries_bp.route('/branches/<branch_id>/summary', methods=['GET'])
def get_branch_summary_endpoint(branch_id):
    """获取分支摘要API"""
    try:
        branch_uuid = uuid.UUID(branch_id)
    except ValueError:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': '无效的分支ID格式'
            }
        }), 400
    
    force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
    
    db: Session = get_db_session()
    
    try:
        summary_data = get_branch_summary(db, branch_uuid, force_refresh=force_refresh)
        
        return jsonify({
            'status': 'success',
            'data': summary_data
        }), 200
    
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'NOT_FOUND',
                'message': str(e)
            }
        }), 404
    except Exception as e:
        import traceback
        if current_app.config.get('FLASK_DEBUG'):
            traceback.print_exc()
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': f'获取摘要失败: {str(e)}'
            }
        }), 500


@summaries_bp.route('/branches/<branch_id>/summary', methods=['POST'])
def generate_branch_summary_endpoint(branch_id):
    """强制生成分支摘要API"""
    try:
        branch_uuid = uuid.UUID(branch_id)
    except ValueError:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': '无效的分支ID格式'
            }
        }), 400
    
    db: Session = get_db_session()
    
    try:
        summary = generate_summary(db, branch_uuid, force=True)
        
        if summary is None:
            return jsonify({
                'status': 'error',
                'error': {
                    'code': 'GENERATION_FAILED',
                    'message': '摘要生成失败，请检查配置或稍后重试'
                }
            }), 500
        
        return jsonify({
            'status': 'success',
            'data': {
                'summary': summary
            }
        }), 200
    
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'NOT_FOUND',
                'message': str(e)
            }
        }), 404
    except Exception as e:
        import traceback
        if current_app.config.get('FLASK_DEBUG'):
            traceback.print_exc()
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': f'生成摘要失败: {str(e)}'
            }
        }), 500
