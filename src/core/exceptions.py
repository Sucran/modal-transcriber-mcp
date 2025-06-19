"""
Custom exceptions for PodcastMCP
"""


class PodcastMCPError(Exception):
    """PodcastMCP基础异常类"""
    pass


class AppError(PodcastMCPError):
    """应用程序异常"""
    pass


class ConfigError(PodcastMCPError):
    """配置相关异常"""
    pass


class ValidationError(PodcastMCPError):
    """验证相关异常"""
    pass


class TranscriptionError(PodcastMCPError):
    """转录相关异常"""
    pass


class DeploymentError(PodcastMCPError):
    """部署相关异常"""
    pass


class FileNotFoundError(PodcastMCPError):
    """文件未找到异常"""
    pass


class EndpointError(PodcastMCPError):
    """Endpoint相关异常"""
    pass 