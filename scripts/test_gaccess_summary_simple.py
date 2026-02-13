#!/usr/bin/env python3
"""简单测试 G-access API 连接和摘要生成"""
import os
import sys
import requests
import json
from pathlib import Path

# 加载 .env 文件
def load_env_file():
    """从项目根目录的 .env 文件加载环境变量"""
    env_file = Path(__file__).parent.parent / '.env'
    if env_file.exists():
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key and value:
                        os.environ.setdefault(key, value)

# 加载环境变量
load_env_file()

def test_gaccess_api():
    """测试 G-access API 连接"""
    
    # 从环境变量读取配置
    gaccess_url = os.getenv('GACCESS_URL', '').strip().rstrip('/')
    gaccess_token = os.getenv('GACCESS_TOKEN', '').strip()
    
    print("=" * 60)
    print("G-access API 测试")
    print("=" * 60)
    print(f"GACCESS_URL: {gaccess_url if gaccess_url else '❌ 未配置'}")
    print(f"GACCESS_TOKEN: {'✅ 已配置' if gaccess_token else '❌ 未配置'}")
    print()
    
    if not gaccess_url or not gaccess_token:
        print("❌ 错误: G-access 未配置")
        print("\n请设置环境变量:")
        print("  export GACCESS_URL='https://your-gaccess-url.com'")
        print("  export GACCESS_TOKEN='your-token'")
        return False
    
    # 测试提示词
    test_prompt = """故事标题：测试故事
故事背景：这是一个测试故事背景
风格：现代风格

前文摘要：（无）

最近续写（共1段）：
【第1段】
这是一个测试续写段，用于验证 G-access API 是否正常工作。

请用中文生成300-500字的故事进展摘要，包括：
1. 当前故事发展到哪里
2. 主要角色及处境
3. 悬而未决的问题

只输出摘要正文。"""
    
    print("发送测试请求...")
    print(f"URL: {gaccess_url}/api/gemini")
    print()
    
    try:
        url = f"{gaccess_url}/api/gemini"
        
        headers = {
            "Authorization": f"Bearer {gaccess_token}",
            "Content-Type": "application/json"
        }
        
        payload = {"prompt": test_prompt}
        
        print("请求内容:")
        print(f"  Prompt长度: {len(test_prompt)} 字符")
        print()
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ API 返回错误状态码: {response.status_code}")
            print(f"响应内容: {response.text[:500]}")
            return False
        
        data = response.json()
        
        # 解析 Gemini 响应格式
        summary = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        
        if not summary:
            print("❌ API 返回空内容")
            print(f"完整响应: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return False
        
        print("✅ API 调用成功!")
        print()
        print("-" * 60)
        print("生成的摘要:")
        print("-" * 60)
        print(summary)
        print("-" * 60)
        print()
        print(f"摘要长度: {len(summary)} 字符")
        
        return True
        
    except requests.exceptions.Timeout:
        print("❌ 请求超时（60秒）")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ 连接错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    if len(sys.argv) > 1 and (sys.argv[1] == '--help' or sys.argv[1] == '-h'):
        print("用法:")
        print("  python scripts/test_gaccess_summary_simple.py")
        print()
        print("环境变量:")
        print("  GACCESS_URL      G-access API URL (例如: https://gaccess.inkpath.cc)")
        print("  GACCESS_TOKEN    G-access 认证 Token")
        print()
        print("示例:")
        print("  export GACCESS_URL='https://gaccess.inkpath.cc'")
        print("  export GACCESS_TOKEN='your-token-here'")
        print("  python scripts/test_gaccess_summary_simple.py")
        sys.exit(0)
    
    success = test_gaccess_api()
    sys.exit(0 if success else 1)
