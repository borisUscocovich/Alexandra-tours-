import json
import os
import time
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

USAGE_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "usage_v2.json")

# Constants from MONETIZATION_v2.md
COSTS = {
    "tts": 0.006,       # per message
    "stt": 0.002,       # per message
    "llm": 0.008,       # per message (approx)
    "weather": 0.0001,  # per call
    "maps": 0.005,      # per call
    "places": 0.017     # per call
}

TIER_LIMITS = {
    "free": {
        "max_interactions": 30,  # Adjusted from 50 as per v2 doc
        "max_cost_eur": 1.0     # Equivalent ~1.00 EUR
    },
    "premium": {
        "max_interactions": 999999,
        "hold_amount_eur": 10.0
    }
}

@dataclass
class UsageItem:
    timestamp: float
    service: str  # "elevenlabs", "claude", "weather", "maps", "places"
    action: str   # "tts", "stt", "completion", "directions"
    cost_eur: float
    cached: bool = False

@dataclass
class SessionUsage:
    session_id: str
    tier: str = "free"
    created_at: str = ""
    last_active: str = ""
    total_cost_eur: float = 0.0
    interaction_count: int = 0
    history: List[UsageItem] = None
    
    def __post_init__(self):
        if self.history is None:
            self.history = []

class UsageCounterService:
    def __init__(self):
        self.db_path = USAGE_DB_PATH
        self._ensure_db()
        self._cache = {} # Simple memory cache to avoid too many reads
        self.reload_db()

    def _ensure_db(self):
        if not os.path.exists(os.path.dirname(self.db_path)):
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        if not os.path.exists(self.db_path):
            with open(self.db_path, "w") as f:
                json.dump({"sessions": {}}, f)

    def reload_db(self):
        try:
            with open(self.db_path, "r") as f:
                data = json.load(f)
                self._cache = {
                    sid: SessionUsage(**s_data) 
                    for sid, s_data in data.get("sessions", {}).items()
                }
                # converting dict history to objects
                for sid in self._cache:
                    history_raw = self._cache[sid].history
                    self._cache[sid].history = [UsageItem(**h) if isinstance(h, dict) else h for h in history_raw]
        except Exception as e:
            print(f"Error loading usage DB: {e}")
            self._cache = {}

    def save_db(self):
        try:
            data = {"sessions": {sid: asdict(usage) for sid, usage in self._cache.items()}}
            with open(self.db_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving usage DB: {e}")

    def get_session(self, session_id: str) -> SessionUsage:
        if session_id not in self._cache:
            self._cache[session_id] = SessionUsage(
                session_id=session_id,
                created_at=datetime.now().isoformat(),
                last_active=datetime.now().isoformat()
            )
        return self._cache[session_id]

    def record_usage(self, session_id: str, service: str, action: str, cost: float = 0.0, cached: bool = False):
        if session_id == "anonymous": return
        
        session = self.get_session(session_id)
        
        # Calculate cost if not provided defaults
        if cost == 0.0 and not cached:
            cost = COSTS.get(service, 0.002) # Default low cost
            if service == "elevenlabs" and action == "tts": cost = COSTS["tts"]
            if service == "claude": cost = COSTS["llm"]
            
        item = UsageItem(
            timestamp=time.time(),
            service=service,
            action=action,
            cost_eur=cost,
            cached=cached
        )
        
        session.history.append(item)
        if not cached:
            session.total_cost_eur += cost
        
        # Count interactions (roughly 1 interaction = 1 LLM or TTS request)
        if service in ["claude", "elevenlabs"] and not cached:
             session.interaction_count += 1
             
        session.last_active = datetime.now().isoformat()
        self.save_db()

    def check_limit(self, session_id: str) -> dict:
        session = self.get_session(session_id)
        limits = TIER_LIMITS.get(session.tier, TIER_LIMITS["free"])
        
        is_limit_reached = False
        remaining = 0
        
        if session.tier == "free":
            is_limit_reached = session.interaction_count >= limits["max_interactions"]
            remaining = limits["max_interactions"] - session.interaction_count
        else:
             # Premium
             remaining = 9999
             is_limit_reached = False

    def get_usage_stats(self, session_id: str) -> dict:
        session = self.get_session(session_id)
        limits = TIER_LIMITS.get(session.tier, TIER_LIMITS["free"])
        
        # Calculate Breakdown
        breakdown = {"voice": 0.0, "intelligence": 0.0, "context": 0.0}
        
        # Determine Period (Last 7 days or since creation)
        # For this MVP, we assume period starts at creation or is just lifetime for now
        # MONETIZATION_v2.md says "Período: 7 días". We can calculate period_start as 7 days ago or creation.
        # Simplification: Period Start = Created At.
        
        for item in session.history:
            if item.service == "elevenlabs":
                breakdown["voice"] += item.cost_eur
            elif item.service == "claude":
                breakdown["intelligence"] += item.cost_eur
            else:
                breakdown["context"] += item.cost_eur
                
        is_limit_reached = False
        limit_val = limits["max_interactions"]
        remaining = 0
        
        if session.tier == "free":
            is_limit_reached = session.interaction_count >= limits["max_interactions"]
            remaining = max(0, limits["max_interactions"] - session.interaction_count)
        else:
            limit_val = 999999
            remaining = 999999
            
        period_end_date = "N/A" # Infinite for now or +7 days
        
        return {
            "session_id": session_id,
            "tier": session.tier,
            "total_cost_eur": round(session.total_cost_eur, 4),
            "interaction_count": session.interaction_count,
            "limit_reached": is_limit_reached,
            "max_interactions": limit_val,
            "remaining": remaining,
            "hold_amount": limits.get("hold_amount_eur", 0),
            "period_start": session.created_at,
            "period_end": period_end_date,
            "breakdown": {k: round(v, 4) for k, v in breakdown.items()}
        }

    def upgrade_user(self, session_id: str):
        session = self.get_session(session_id)
        session.tier = "premium"
        self.save_db()
        return session

usage_counter = UsageCounterService()
