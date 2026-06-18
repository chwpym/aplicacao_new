import httpx
import time
from typing import Dict
from app.services.logging_service import logger

class StatusService:
    _instance = None
    _cache = {}
    _cache_time = 0
    CACHE_DURATION = 600  # 10 minutos

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StatusService, cls).__new__(cls)
        return cls._instance

    async def get_system_status(self) -> Dict[str, str]:
        current_time = time.time()
        
        # Retorna cache se ainda for válido
        if self._cache and (current_time - self._cache_time < self.CACHE_DURATION):
            return self._cache

        status = {
            "fipe": "offline",
            "overall": "healthy"
        }

        async with httpx.AsyncClient(timeout=5.0) as client:
            # Check FIPE (Parallelum)
            try:
                # Usamos um endpoint simples de marcas para teste
                resp = await client.get("https://fipe.parallelum.com.br/api/v2/cars/brands")
                if resp.status_code == 200:
                    status["fipe"] = "online"
                else:
                    status["fipe"] = "unstable"
            except Exception as e:
                logger.warning("HEALTH", f"FIPE Check falhou: {e}")
                status["fipe"] = "offline"

        # Define status geral baseado apenas na FIPE
        if status["fipe"] == "online":
            status["overall"] = "healthy"
        elif status["fipe"] == "unstable":
            status["overall"] = "warning"
        else:
            status["overall"] = "critical"

        self._cache = status
        self._cache_time = current_time
        return status

status_service = StatusService()
