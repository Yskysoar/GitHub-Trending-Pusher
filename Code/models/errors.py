class AppError(Exception):
    """应用基础异常类。"""

    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(self.message)


class GitHubAPIError(AppError):
    """GitHub API调用异常。错误码范围: 1001-1999"""

    pass


class LLMError(AppError):
    """LLM调用异常。错误码范围: 2001-2999"""

    pass


class DatabaseError(AppError):
    """数据库操作异常。错误码范围: 3001-3999"""

    pass


class EvalError(AppError):
    """综合评估异常。错误码范围: 3501-3599"""

    pass


class RuleError(AppError):
    """规则配置异常。错误码范围: 4001-4999"""

    pass


class FileError(AppError):
    """文件操作异常。错误码范围: 5001-5999"""

    pass


class AutoStartError(AppError):
    """开机自启动异常。错误码范围: 6001-6999"""

    pass


class ErrorCode:
    """错误码常量定义。"""

    GITHUB_API_ERROR = 1001
    GITHUB_RATE_LIMIT = 1002
    GITHUB_TOKEN_INVALID = 1003

    LLM_API_ERROR = 2001
    LLM_TIMEOUT = 2002
    LLM_API_KEY_INVALID = 2003

    DB_ERROR = 3001

    EVAL_ERROR = 3501
    EVAL_WEIGHT_INVALID = 3502

    RULE_INVALID = 4001
    RULE_NOT_FOUND = 4002

    FILE_SAVE_ERROR = 5001
    DIR_NOT_FOUND = 5002

    AUTOSTART_ERROR = 6001
