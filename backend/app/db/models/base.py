"""SQLAlchemy base class and portable types for all models."""

import uuid
from typing import Optional

from sqlalchemy import String, TypeDecorator
from sqlalchemy.orm import DeclarativeBase


class GUID(TypeDecorator):
    """Platform-independent UUID type.
    Uses String(36) to store UUID on SQLite, maps to native UUID on PostgreSQL.
    """
    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return uuid.UUID(value)
        return value


class Base(DeclarativeBase):
    pass
