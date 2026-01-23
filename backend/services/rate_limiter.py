import time
from collections import defaultdict

class UserRateLimiter:
    """Limita requests por usuario/sesión."""

    def __init__(self):
        self._requests = defaultdict(list)

    # Límites por tier
    LIMITS = {
        "free": {
            "requests_per_hour": 20,
            "requests_per_day": 50,
            "max_conversation_turns": 15
        },
        "premium": {
            "requests_per_hour": 200,
            "requests_per_day": 1000,
            "max_conversation_turns": 100
        }
    }

    def check_limit(self, user_id: str, tier: str = "free") -> dict:
        now = time.time()
        hour_ago = now - 3600
        day_ago = now - 86400

        # Limpiar requests viejos
        self._requests[user_id] = [
            t for t in self._requests[user_id] if t > day_ago
        ]

        requests = self._requests[user_id]
        hourly = len([t for t in requests if t > hour_ago])
        daily = len(requests)

        limits = self.LIMITS.get(tier, self.LIMITS["free"])

        if hourly >= limits["requests_per_hour"]:
            return {
                "allowed": False,
                "reason": "hourly_limit",
                "reset_in": int(min(requests) + 3600 - now) if requests else 60,
                "message": "Has alcanzado el límite por hora. Prueba en unos minutos o hazte premium."
            }

        if daily >= limits["requests_per_day"]:
            return {
                "allowed": False,
                "reason": "daily_limit",
                "reset_in": int(min(requests) + 86400 - now) if requests else 3600,
                "message": "Límite diario alcanzado. Vuelve mañana o hazte premium para más."
            }

        return {"allowed": True}

    def record_request(self, user_id: str):
        self._requests[user_id].append(time.time())

    def get_usage(self, user_id: str, tier: str = "free") -> dict:
        now = time.time()
        requests = self._requests.get(user_id, [])
        hourly = len([t for t in requests if t > now - 3600])
        daily = len([t for t in requests if t > now - 86400])
        limits = self.LIMITS.get(tier, self.LIMITS["free"])

        return {
            "hourly": {"used": hourly, "limit": limits["requests_per_hour"]},
            "daily": {"used": daily, "limit": limits["requests_per_day"]}
        }

rate_limiter = UserRateLimiter()
