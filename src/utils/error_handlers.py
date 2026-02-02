"""错误处理"""
from flask import jsonify


def register_error_handlers(app):
    """注册错误处理器"""
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'status': 'error',
            'message': 'Resource not found'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            'status': 'error',
            'message': 'Bad request'
        }), 400
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'RATE_LIMIT_EXCEEDED',
                'message': '速率限制已超出，请稍后再试'
            }
        }), 429
    
    @app.errorhandler(422)
    def unprocessable_entity(error):
        """处理422错误（连续性校验失败等）"""
        from werkzeug.exceptions import UnprocessableEntity
        message = error.description if hasattr(error, 'description') else '请求无法处理'
        return jsonify({
            'status': 'error',
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': message
            }
        }), 422
