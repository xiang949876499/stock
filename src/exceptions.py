"""自定义异常"""


class StockHubException(Exception):
    """Stock Hub 基础异常"""

    def __init__(self, code: int = 500, message: str = "服务器内部错误"):
        self.code = code
        self.message = message
        super().__init__(message)


class ValidationError(StockHubException):
    """验证错误"""

    def __init__(self, message: str = "数据验证失败"):
        super().__init__(code=400, message=message)


class NotFoundError(StockHubException):
    """资源不存在"""

    def __init__(self, message: str = "资源不存在"):
        super().__init__(code=404, message=message)


class UnauthorizedError(StockHubException):
    """未授权"""

    def __init__(self, message: str = "未授权"):
        super().__init__(code=401, message=message)


class ForbiddenError(StockHubException):
    """禁止访问"""

    def __init__(self, message: str = "禁止访问"):
        super().__init__(code=403, message=message)


class DataProviderError(StockHubException):
    """数据源错误"""

    def __init__(self, message: str = "数据源错误"):
        super().__init__(code=502, message=message)


class AIProviderError(StockHubException):
    """AI 提供商错误"""

    def __init__(self, message: str = "AI 提供商错误"):
        super().__init__(code=502, message=message)


class SignalError(StockHubException):
    """信号错误"""

    def __init__(self, message: str = "信号错误"):
        super().__init__(code=400, message=message)


class RiskCheckError(StockHubException):
    """风控检查错误"""

    def __init__(self, message: str = "风控检查失败"):
        super().__init__(code=403, message=message)
