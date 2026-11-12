import asyncio
from typing import List, Dict, Any
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    Frontend uchun real-time WebSocket menejeri.
    Yangi kirish-chiqish hodisalari yuz berganda barcha ulangan brauzerlarga xabar tarqatadi.
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Yangi WebSocket mijozi ulandi. Jami: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket mijozi uzildi. Qoldi: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        """Barcha ulangan mijozlarga JSON xabar yuborish"""
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"WebSocket uzatishda xatolik: {e}")
                self.disconnect(connection)

ws_manager = ConnectionManager()
