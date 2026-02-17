"""数据模型模块"""
from src.models.user import User
from src.models.agent import Agent
from src.models.story import Story
from src.models.branch import Branch
from src.models.segment import Segment
from src.models.segment_log import SegmentLog
from src.models.pinned_post import PinnedPost
from src.models.bot_branch_membership import BotBranchMembership
from src.models.human_branch_membership import HumanBranchMembership
from src.models.vote import Vote
from src.models.comment import Comment
from src.models.bot_reputation_log import BotReputationLog

# 兼容旧代码 - Bot = Agent
Bot = Agent

__all__ = [
    'User',
    'Agent',
    'Bot',
    'Story',
    'Branch',
    'Segment',
    'SegmentLog',
    'PinnedPost',
    'BotBranchMembership',
    'HumanBranchMembership',
    'Vote',
    'Comment',
    'BotReputationLog',
]
