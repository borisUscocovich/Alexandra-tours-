from backend.services.usage_counter import usage_counter

class UserRateLimiter:
    """
    Limita requests basándose en el UsageCounter persistente.
    Adhiere a la lógica v2: Freemium persistente (no reset diario).
    """

    def check_limit(self, user_id: str, tier: str = "free") -> dict:
        # Sync tier in usage counter if different (or just rely on usage counter's stored tier)
        # For now, we assume usage_counter handles the source of truth for tier, 
        # but if the request claims a tier, we might want to respect it or validate it.
        # In v2, the session determines the tier, not the request parameter ideally.
        
        status = usage_counter.check_limit(user_id)
        
        if not status["allowed"]:
            return {
                "allowed": False,
                "reason": "limit_reached",
                "reset_in": 0, # Never resets automatically in v2 Free tier
                "message": f"Has alcanzado el límite gratuito ({status['interaction_count']}/{status['limit']}). Pásate a Premium para continuar."
            }
            
        return {"allowed": True}

    def record_request(self, user_id: str):
        # This is now handled by usage_counter.record_usage calling explicitly in routes
        # But for compatibility with existing calls:
        pass 

    def get_usage(self, user_id: str, tier: str = "free") -> dict:
        session = usage_counter.get_session(user_id)
        return {
            "total_cost": session.total_cost_eur,
            "interactions": session.interaction_count,
            "tier": session.tier
        }

rate_limiter = UserRateLimiter()
