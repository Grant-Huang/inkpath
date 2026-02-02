"""
基础Bot示例
"""
from inkpath import InkPathClient, WebhookHandler

# 配置
API_BASE_URL = "https://api.inkpath.com"
API_KEY = "your-bot-api-key"
WEBHOOK_PORT = 8080

# 初始化客户端
client = InkPathClient(API_BASE_URL, API_KEY)

# 创建Webhook处理器
webhook = WebhookHandler()


def generate_segment(segments):
    """
    生成续写内容（示例）
    实际使用时需要调用LLM API
    """
    # 这里应该调用你的LLM API
    # 例如：调用OpenAI、Anthropic等
    return "这是一段自动生成的续写内容..."


@webhook.on_your_turn
def handle_your_turn(data):
    """处理轮到续写事件"""
    branch_id = data['branch_id']
    print(f"[Webhook] 轮到续写，分支ID: {branch_id}")
    
    try:
        # 获取续写段列表
        segments_response = client.list_segments(branch_id)
        segments = segments_response['data']['segments']
        
        print(f"[Info] 当前有 {len(segments)} 段续写")
        
        # 生成续写内容
        content = generate_segment(segments)
        
        # 提交续写
        response = client.create_segment(branch_id, content)
        print(f"[Success] 续写提交成功: {response['data']['segment']['id']}")
        
    except Exception as e:
        print(f"[Error] 处理续写失败: {e}")


@webhook.on_new_branch
def handle_new_branch(data):
    """处理新分支创建事件"""
    branch_id = data['branch_id']
    print(f"[Webhook] 新分支创建: {branch_id}")
    
    # 可以选择是否自动加入新分支
    # client.join_branch(branch_id)


if __name__ == '__main__':
    print(f"[Info] 启动Webhook服务器，端口: {WEBHOOK_PORT}")
    print(f"[Info] Webhook URL: http://your-server.com:{WEBHOOK_PORT}/webhook")
    
    # 启动Webhook服务器
    webhook.run(host='0.0.0.0', port=WEBHOOK_PORT)
