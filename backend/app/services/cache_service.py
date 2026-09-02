import time
from typing import Any, Optional


class CacheService:
    def __init__(self, expiration_seconds: int = 300):  # Default 5 minutos
        self._cache = {}
        self._expiration = expiration_seconds

    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self._expiration:
                return data
            else:
                del self._cache[key]
        return None

    def set(self, key: str, value: Any):
        self._cache[key] = (value, time.time())

    def clear(self):
        self._cache = {}


# Singleton para uso em toda a aplicação
cache_service = CacheService()
