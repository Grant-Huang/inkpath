#!/usr/bin/env python3
"""测试使用 G-access 生成当前进展提要"""
import os
import sys
import uuid
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

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import get_db
from src.services.summary_service import generate_summary_with_gaccess, get_branch_summary
from src.config import Config


def test_gaccess_summary(branch_id: str = None):
    """测试使用 G-access 生成摘要"""
    
    # 检查配置
    gaccess_url = getattr(Config, 'GACCESS_URL', '').strip()
    gaccess_token = getattr(Config, 'GACCESS_TOKEN', '').strip()
    
    print("=" * 60)
    print("G-access 配置检查")
    print("=" * 60)
    print(f"GACCESS_URL: {gaccess_url if gaccess_url else '❌ 未配置'}")
    print(f"GACCESS_TOKEN: {'✅ 已配置' if gaccess_token else '❌ 未配置'}")
    print(f"LLM_PROVIDER: {getattr(Config, 'LLM_PROVIDER', 'gaccess')}")
    print()
    
    if not gaccess_url or not gaccess_token:
        print("❌ 错误: G-access 未配置")
        print("\n请设置环境变量:")
        print("  export GACCESS_URL='https://your-gaccess-url.com'")
        print("  export GACCESS_TOKEN='your-token'")
        return
    
    # 获取数据库会话
    db = next(get_db())
    
    # 如果没有提供分支ID，尝试查找一个活跃的分支
    if not branch_id:
        from src.models.branch import Branch
        from src.models.segment import Segment
        
        # 查找有续写段的分支
        branch = db.query(Branch).join(Segment).filter(
            Branch.status == 'active'
        ).first()
        
        if not branch:
            print("❌ 错误: 没有找到包含续写段的活跃分支")
            print("\n请指定一个分支ID:")
            print("  python scripts/test_gaccess_summary.py <branch_id>")
            return
        
        branch_id = str(branch.id)
        print(f"✅ 自动选择分支: {branch.title} ({branch_id})")
    else:
        try:
            branch_uuid = uuid.UUID(branch_id)
            from src.models.branch import Branch
            branch = db.query(Branch).filter(Branch.id == branch_uuid).first()
            if not branch:
                print(f"❌ 错误: 分支 {branch_id} 不存在")
                return
            print(f"✅ 使用分支: {branch.title} ({branch_id})")
        except ValueError:
            print(f"❌ 错误: 无效的分支ID格式: {branch_id}")
            return
    
    branch_uuid = uuid.UUID(branch_id)
    
    # 检查续写段数量
    from src.models.segment import Segment
    segments_count = db.query(Segment).filter(Segment.branch_id == branch_uuid).count()
    print(f"📝 续写段数量: {segments_count}")
    
    if segments_count == 0:
        print("❌ 错误: 该分支没有续写段，无法生成摘要")
        return
    
    print()
    print("=" * 60)
    print("开始生成摘要...")
    print("=" * 60)
    print()
    
    try:
        # 使用 g-access 生成摘要
        summary = generate_summary_with_gaccess(db, branch_uuid)
        
        if summary:
            print("✅ 摘要生成成功!")
            print()
            print("-" * 60)
            print("生成的摘要:")
            print("-" * 60)
            print(summary)
            print("-" * 60)
            print()
            
            # 获取完整的摘要信息（包括更新时间等）
            summary_info = get_branch_summary(db, branch_uuid, force_refresh=False)
            print(f"📅 更新时间: {summary_info.get('updated_at', 'N/A')}")
            print(f"📊 覆盖到第 {summary_info.get('covers_up_to', 0)} 段")
        else:
            print("❌ 摘要生成失败: 返回空内容")
            print("\n可能的原因:")
            print("  1. G-access API 返回了空响应")
            print("  2. API 响应格式不符合预期")
            print("  3. 网络连接问题")
            
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == '__main__':
    branch_id = sys.argv[1] if len(sys.argv) > 1 else None
    
    if branch_id == '--help' or branch_id == '-h':
        print("用法:")
        print("  python scripts/test_gaccess_summary.py [branch_id]")
        print()
        print("参数:")
        print("  branch_id  (可选) 分支UUID，如果不提供则自动选择第一个有续写段的分支")
        print()
        print("环境变量:")
        print("  GACCESS_URL      G-access API URL")
        print("  GACCESS_TOKEN    G-access 认证 Token")
        print("  LLM_PROVIDER     LLM提供商 (默认: gaccess)")
        sys.exit(0)
    
    test_gaccess_summary(branch_id)
