from sqlalchemy.ext.asyncio import AsyncSession

from extractor.core.logging import LoggerMixin


class BaseRepository(LoggerMixin):
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
