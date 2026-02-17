"""Bot 模型 - 已废弃，请使用 Agent

此文件已弃用，仅用于向后兼容。
请使用 from src.models.agent import Agent
"""
from src.models.agent import Agent

# 向后兼容
Bot = Agent

__all__ = ['Agent', 'Bot']
