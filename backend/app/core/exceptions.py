"""Custom exception classes for the application."""

from fastapi import HTTPException, status


class AppException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


class NotFound(AppException):
    def __init__(self, detail: str = "资源不存在"):
        super().__init__(status.HTTP_404_NOT_FOUND, detail)


class Unauthorized(AppException):
    def __init__(self, detail: str = "未认证"):
        super().__init__(status.HTTP_401_UNAUTHORIZED, detail)


class Forbidden(AppException):
    def __init__(self, detail: str = "无权限"):
        super().__init__(status.HTTP_403_FORBIDDEN, detail)


class Conflict(AppException):
    def __init__(self, detail: str = "资源冲突"):
        super().__init__(status.HTTP_409_CONFLICT, detail)


class BadRequest(AppException):
    def __init__(self, detail: str = "请求参数错误"):
        super().__init__(status.HTTP_400_BAD_REQUEST, detail)


class RateLimited(AppException):
    def __init__(self, detail: str = "请求频率过高，请稍后重试"):
        super().__init__(status.HTTP_429_TOO_MANY_REQUESTS, detail)
