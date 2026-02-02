"""Flask应用主入口"""
from flask import Flask
from flask_cors import CORS
from src.config import Config


def create_app(config_class=Config):
    """应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 配置JWT
    app.config['JWT_SECRET_KEY'] = config_class.JWT_SECRET_KEY
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = config_class.JWT_ACCESS_TOKEN_EXPIRES
    
    # 初始化JWT
    from src.utils.auth import init_jwt
    init_jwt(app)
    
    # 初始化速率限制器
    from src.utils.rate_limit import limiter
    limiter.init_app(app)
    
    # 启用CORS
    CORS(app)
    
    # 注册蓝图
    from src.api.v1.health import health_bp
    from src.api.v1.auth import auth_bp
    from src.api.v1.stories import stories_bp
    from src.api.v1.pinned_posts import pinned_posts_bp
    from src.api.v1.branches import branches_bp
    from src.api.v1.segments import segments_bp
    from src.api.v1.votes import votes_bp
    from src.api.v1.reputation import reputation_bp
    from src.api.v1.webhooks import webhooks_bp
    from src.api.v1.summaries import summaries_bp
    from src.api.v1.comments import comments_bp
    from src.api.v1.cron import cron_bp
    app.register_blueprint(health_bp, url_prefix='/api/v1')
    app.register_blueprint(auth_bp, url_prefix='/api/v1')
    app.register_blueprint(stories_bp, url_prefix='/api/v1')
    app.register_blueprint(pinned_posts_bp, url_prefix='/api/v1')
    app.register_blueprint(branches_bp, url_prefix='/api/v1')
    app.register_blueprint(segments_bp, url_prefix='/api/v1')
    app.register_blueprint(votes_bp, url_prefix='/api/v1')
    app.register_blueprint(reputation_bp, url_prefix='/api/v1')
    app.register_blueprint(webhooks_bp, url_prefix='/api/v1')
    app.register_blueprint(summaries_bp, url_prefix='/api/v1')
    app.register_blueprint(comments_bp, url_prefix='/api/v1')
    app.register_blueprint(cron_bp, url_prefix='/api/v1')
    
    # 注册错误处理
    from src.utils.error_handlers import register_error_handlers
    register_error_handlers(app)
    
    # 初始化定时任务调度器（如果启用）
    from src.scheduler import init_scheduler
    scheduler = init_scheduler(app)
    if scheduler:
        app.config['SCHEDULER'] = scheduler
    
    return app


if __name__ == '__main__':
    import os
    app = create_app()
    port = int(os.getenv('PORT', 5002))  # Flask API 运行在 5002 端口（5000 被 AirPlay 占用）
    app.run(debug=True, host='0.0.0.0', port=port)
