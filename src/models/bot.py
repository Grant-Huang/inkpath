# Bot 模型 - 已废弃，请直接使用 Agent
# 此文件仅用于向后兼容
# 新代码请使用：from src.models.agent import Agent

# 延迟导入避免问题
import sys

def __getattr__(name):
    if name == 'Bot':
        from src.models.agent import Agent
        return Agent
    if name == 'Agent':
        from src.models.agent import Agent
        return Agent
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

def __dir__():
    return ['Agent', 'Bot']
