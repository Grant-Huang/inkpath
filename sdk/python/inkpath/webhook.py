"""
Webhook处理工具
"""
from flask import Flask, request, jsonify
from typing import Callable, Optional, Dict, Any
import logging


class WebhookHandler:
    """Webhook处理器"""
    
    def __init__(self, secret: Optional[str] = None):
        """
        初始化Webhook处理器
        
        Args:
            secret: Webhook密钥（可选，用于验证请求）
        """
        self.secret = secret
        self.handlers: Dict[str, Callable] = {}
        self.app = Flask(__name__)
        self._setup_routes()
    
    def _setup_routes(self):
        """设置路由"""
        @self.app.route('/webhook', methods=['POST'])
        def webhook():
            return self._handle_webhook()
    
    def _handle_webhook(self):
        """处理Webhook请求"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Invalid JSON'}), 400
            
            event = data.get('event')
            if not event:
                return jsonify({'error': 'Missing event field'}), 400
            
            # 调用对应的处理器
            handler = self.handlers.get(event)
            if handler:
                try:
                    handler(data)
                    return jsonify({'status': 'ok'}), 200
                except Exception as e:
                    logging.error(f"Webhook handler error: {e}")
                    return jsonify({'error': 'Handler error'}), 500
            else:
                logging.warning(f"Unknown webhook event: {event}")
                return jsonify({'status': 'ok'}), 200  # 未知事件也返回200，避免重试
        
        except Exception as e:
            logging.error(f"Webhook processing error: {e}")
            return jsonify({'error': 'Internal error'}), 500
    
    def on_your_turn(self, handler: Callable[[Dict[str, Any]], None]):
        """
        注册"轮到续写"事件处理器
        
        Args:
            handler: 处理函数，接收事件数据字典
        """
        self.handlers['your_turn'] = handler
    
    def on_new_branch(self, handler: Callable[[Dict[str, Any]], None]):
        """
        注册"新分支创建"事件处理器
        
        Args:
            handler: 处理函数，接收事件数据字典
        """
        self.handlers['new_branch'] = handler
    
    def run(self, host: str = '0.0.0.0', port: int = 8080, debug: bool = False):
        """
        启动Webhook服务器
        
        Args:
            host: 监听地址
            port: 监听端口
            debug: 是否启用调试模式
        """
        self.app.run(host=host, port=port, debug=debug)
