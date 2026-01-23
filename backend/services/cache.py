import time
from typing import Optional, Any
import hashlib

class SmartCache:
    """In-memory cache con TTL. Escala a Redis después."""

    def __init__(self):
        self._cache = {}
        self._hits = 0
        self._misses = 0

    def _hash_key(self, key: str) -> str:
        return hashlib.md5(key.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        hashed = self._hash_key(key)
        if hashed in self._cache:
            entry = self._cache[hashed]
            if entry['expires'] > time.time():
                self._hits += 1
                return entry['value']
            else:
                del self._cache[hashed]
        self._misses += 1
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        hashed = self._hash_key(key)
        self._cache[hashed] = {
            'value': value,
            'expires': time.time() + ttl_seconds
        }

    def stats(self):
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        return {"hits": self._hits, "misses": self._misses, "hit_rate": f"{hit_rate:.1f}%"}

# Singleton
cache = SmartCache()

# TTLs por tipo de dato
CACHE_TTL = {
    "weather": 600,        # 10 min (clima cambia lento)
    "places": 3600,        # 1 hora (lugares no cambian)
    "events": 1800,        # 30 min (eventos del día)
    "city_context": 300,   # 5 min (contexto general)
    "faq": 86400,          # 24h (FAQs estáticas)
}
