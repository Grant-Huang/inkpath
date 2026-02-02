"""
InkPath Python SDK

官方Python SDK，简化Bot开发。
"""

__version__ = "0.1.0"

from .client import InkPathClient
from .webhook import WebhookHandler

__all__ = ['InkPathClient', 'WebhookHandler']
