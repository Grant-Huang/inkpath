"""
InkPath SDK异常类
"""


class InkPathError(Exception):
    """InkPath SDK基础异常"""
    pass


class APIError(InkPathError):
    """API调用错误"""
    def __init__(self, message: str, code: str = "API_ERROR", status_code: int = 0):
        self.message = message
        self.code = code
        self.status_code = status_code
        super().__init__(f"[{code}] {message}")


class ValidationError(InkPathError):
    """请求验证错误（422）"""
    def __init__(self, message: str, code: str = "VALIDATION_ERROR"):
        self.message = message
        self.code = code
        super().__init__(f"[{code}] {message}")
