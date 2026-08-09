from typing import Dict, Any
from app.core.di.container import get_container
from app.services.ai.orchestrator import AIOrchestrator
import logging

logger = logging.getLogger(__name__)


class MessageProcessorUseCase:
    def __init__(self):
        self._container = get_container()
        self._orchestrator = AIOrchestrator()

    async def process(self, user_id: int, message: str) -> Dict[str, Any]:
        from app.database import async_session_factory

        async with async_session_factory() as db:
            return await self._orchestrator.process_message(
                user_id=user_id,
                message=message,
                db=db,
            )
