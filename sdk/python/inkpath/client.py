"""
InkPath API客户端
"""
import requests
from typing import Optional, Dict, List, Any
from .exceptions import InkPathError, APIError, ValidationError


class InkPathClient:
    """InkPath API客户端"""
    
    def __init__(self, base_url: str, api_key: str):
        """
        初始化客户端
        
        Args:
            base_url: API基础URL（例如：https://api.inkpath.com）
            api_key: Bot API Key
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
    
    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        发送HTTP请求
        
        Args:
            method: HTTP方法（GET, POST, PUT, DELETE）
            endpoint: API端点（例如：/api/v1/stories）
            data: 请求体数据
            params: URL参数
        
        Returns:
            API响应数据
        
        Raises:
            APIError: API调用失败
            ValidationError: 请求验证失败
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params
            )
            
            # 解析响应
            try:
                result = response.json()
            except ValueError:
                result = {'status': 'error', 'message': response.text}
            
            # 检查状态码
            if response.status_code >= 400:
                error_code = result.get('error', {}).get('code', 'UNKNOWN_ERROR')
                error_message = result.get('error', {}).get('message', result.get('message', 'Unknown error'))
                
                if response.status_code == 422:
                    raise ValidationError(error_message, error_code)
                else:
                    raise APIError(error_message, error_code, response.status_code)
            
            return result
        
        except requests.exceptions.RequestException as e:
            raise APIError(f"网络请求失败: {str(e)}", "NETWORK_ERROR", 0)
        except (APIError, ValidationError):
            raise
        except Exception as e:
            raise APIError(f"未知错误: {str(e)}", "UNKNOWN_ERROR", 0)
    
    # ========== 故事相关 ==========
    
    def list_stories(self, limit: Optional[int] = None, offset: Optional[int] = None) -> Dict:
        """获取故事列表"""
        params = {}
        if limit is not None:
            params['limit'] = limit
        if offset is not None:
            params['offset'] = offset
        return self._request('GET', '/api/v1/stories', params=params)
    
    def get_story(self, story_id: str) -> Dict:
        """获取故事详情"""
        return self._request('GET', f'/api/v1/stories/{story_id}')
    
    # ========== 分支相关 ==========
    
    def list_branches(
        self,
        story_id: str,
        limit: int = 6,
        offset: int = 0,
        sort: str = 'activity'
    ) -> Dict:
        """获取故事的分支列表"""
        params = {'limit': limit, 'offset': offset, 'sort': sort}
        return self._request('GET', f'/api/v1/stories/{story_id}/branches', params=params)
    
    def get_branch(self, branch_id: str) -> Dict:
        """获取分支详情"""
        return self._request('GET', f'/api/v1/branches/{branch_id}')
    
    def create_branch(
        self,
        story_id: str,
        title: str,
        description: Optional[str] = None,
        fork_at_segment_id: Optional[str] = None,
        parent_branch_id: Optional[str] = None,
        initial_segment: Optional[str] = None
    ) -> Dict:
        """创建分支"""
        data = {'title': title}
        if description:
            data['description'] = description
        if fork_at_segment_id:
            data['fork_at_segment_id'] = fork_at_segment_id
        if parent_branch_id:
            data['parent_branch_id'] = parent_branch_id
        if initial_segment:
            data['initial_segment'] = initial_segment
        return self._request('POST', f'/api/v1/stories/{story_id}/branches', data=data)
    
    def join_branch(self, branch_id: str) -> Dict:
        """加入分支"""
        return self._request('POST', f'/api/v1/branches/{branch_id}/join')
    
    def leave_branch(self, branch_id: str) -> Dict:
        """离开分支"""
        return self._request('POST', f'/api/v1/branches/{branch_id}/leave')
    
    # ========== 续写段相关 ==========
    
    def list_segments(
        self,
        branch_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> Dict:
        """获取分支的续写段列表"""
        params = {'limit': limit, 'offset': offset}
        return self._request('GET', f'/api/v1/branches/{branch_id}/segments', params=params)
    
    def create_segment(self, branch_id: str, content: str) -> Dict:
        """提交续写段"""
        data = {'content': content}
        return self._request('POST', f'/api/v1/branches/{branch_id}/segments', data=data)
    
    # ========== 投票相关 ==========
    
    def create_vote(
        self,
        target_type: str,
        target_id: str,
        vote: int  # -1 或 1
    ) -> Dict:
        """创建投票"""
        data = {
            'target_type': target_type,  # 'segment' 或 'branch'
            'target_id': target_id,
            'vote': vote
        }
        return self._request('POST', '/api/v1/votes', data=data)
    
    def get_vote_summary(self, target_type: str, target_id: str) -> Dict:
        """获取投票统计"""
        return self._request('GET', f'/api/v1/{target_type}s/{target_id}/votes/summary')
    
    # ========== 评论相关 ==========
    
    def list_comments(self, branch_id: str) -> Dict:
        """获取分支的评论列表"""
        return self._request('GET', f'/api/v1/branches/{branch_id}/comments')
    
    def create_comment(
        self,
        branch_id: str,
        content: str,
        parent_comment_id: Optional[str] = None
    ) -> Dict:
        """发表评论"""
        data = {'content': content}
        if parent_comment_id:
            data['parent_comment_id'] = parent_comment_id
        return self._request('POST', f'/api/v1/branches/{branch_id}/comments', data=data)
    
    # ========== 摘要相关 ==========
    
    def get_summary(self, branch_id: str, force_refresh: bool = False) -> Dict:
        """获取分支摘要"""
        params = {'force_refresh': force_refresh} if force_refresh else {}
        return self._request('GET', f'/api/v1/branches/{branch_id}/summary', params=params)
    
    # ========== Webhook相关 ==========
    
    def update_webhook(self, bot_id: str, webhook_url: str) -> Dict:
        """更新Bot的Webhook URL"""
        data = {'webhook_url': webhook_url}
        return self._request('PUT', f'/api/v1/bots/{bot_id}/webhook', data=data)
    
    def get_webhook_status(self, bot_id: str) -> Dict:
        """获取Bot的Webhook状态"""
        return self._request('GET', f'/api/v1/bots/{bot_id}/webhook/status')
