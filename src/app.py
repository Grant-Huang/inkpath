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
    
    # 启用CORS（允许多个域名）
    CORS(app, resources={
        r"/api/*": {
            "origins": [
                "http://localhost:3000",
                "https://inkpath.vercel.app", 
                "https://inkpath-git-main-grant-huangs-projects.vercel.app",
                "https://www.inkpath.cc",
                "https://inkpath.cc"
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,
            "max_age": 3600
        }
    })
    
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
    from src.api.v1.config import config_bp
    from src.api.v1.rewrites import rewrites_bp
    from src.api.v1.agent import agent_bp
    from src.api.v1.admin import admin_bp
    from src.api.v1.dashboard import dashboard_bp
    from src.api.v1.logs import logs_bp
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
    app.register_blueprint(config_bp, url_prefix='/api/v1')
    app.register_blueprint(rewrites_bp, url_prefix='/api/v1')
    app.register_blueprint(agent_bp, url_prefix='/api/v1')
    app.register_blueprint(admin_bp, url_prefix='/api/v1')
    app.register_blueprint(dashboard_bp, url_prefix='/api/v1')
    app.register_blueprint(logs_bp, url_prefix='/api/v1')
    app.register_blueprint(dashboard_bp, url_prefix='/api/v1')
    
    # 注册错误处理
    from src.utils.error_handlers import register_error_handlers
    register_error_handlers(app)
    
    # 初始化定时任务调度器（如果启用）
    from src.scheduler import init_scheduler
    scheduler = init_scheduler(app)
    if scheduler:
        app.config['SCHEDULER'] = scheduler
    
    # .well-known 端点 - 提供 Agent 规范
    from flask import send_from_directory, jsonify
    import os
    wellknown_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.well-known')
    
    @app.route('/.well-known/<path:filename>')
    def serve_wellknown(filename):
        """提供 .well-known 文件夹中的文件"""
        return send_from_directory(wellknown_dir, filename)
    
    @app.route('/.well-known/')
    def wellknown_index():
        """列出 .well-known 文件夹中的可用规范"""
        import json
        specs = []
        if os.path.exists(wellknown_dir):
            for f in os.listdir(wellknown_dir):
                if f.endswith('.json'):
                    specs.append({
                        "file": f"/.well-known/{f}",
                        "description": f"InkPath Agent Specification: {f}"
                    })
        return jsonify({
            "name": "InkPath Agent Specifications",
            "version": "1.0.0",
            "specs": specs
        })
    
    return app


if __name__ == '__main__':
    import os
    app = create_app()
    port = int(os.getenv('PORT', 5002))  # Flask API 运行在 5002 端口（5000 被 AirPlay 占用）
    app.run(debug=True, host='0.0.0.0', port=port)
