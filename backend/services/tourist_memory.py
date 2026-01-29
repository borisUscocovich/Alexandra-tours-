import json
import os
import time
from typing import List, Dict, Optional
from dataclasses import dataclass, field, asdict

SESSIONS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "sessions")

@dataclass
class TouristPreferences:
    food_types: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)
    price_range: str = "medium" # low, medium, high
    trip_type: str = "solo" # solo, couple, group, family
    language: str = "es"

@dataclass
class Interaction:
    timestamp: float
    role: str
    content: str
    intent: Optional[str] = None

@dataclass
class PlaceStatus:
    status: str # recommended, visited, rejected
    timestamp: float

@dataclass
class SessionData:
    session_id: str
    created_at: str
    last_interaction: str
    tier: str = "free"
    email: Optional[str] = None
    preferences: TouristPreferences = field(default_factory=TouristPreferences)
    interactions: List[Interaction] = field(default_factory=list)
    places_discussed: Dict[str, PlaceStatus] = field(default_factory=dict)
    context_summary: str = ""

class TouristMemory:
    """
    Manages persistent memory for a tourist session.
    Replaces the ephemeral conversation_state.
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.file_path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
        self.data = self._load()

    def _load(self) -> SessionData:
        """Loads session data from JSON or creates new."""
        if not os.path.exists(SESSIONS_DIR):
            os.makedirs(SESSIONS_DIR, exist_ok=True)
            
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    raw = json.load(f)
                    # Reconstruct objects
                    prefs = TouristPreferences(**raw.get("preferences", {}))
                    interactions = [Interaction(**i) for i in raw.get("interactions", [])]
                    places = {k: PlaceStatus(**v) for k, v in raw.get("places_discussed", {}).items()}
                    
                    return SessionData(
                        session_id=raw["session_id"],
                        created_at=raw["created_at"],
                        last_interaction=raw.get("last_interaction", raw["created_at"]),
                        tier=raw.get("tier", "free"),
                        email=raw.get("email"),
                        preferences=prefs,
                        interactions=interactions,
                        places_discussed=places,
                        context_summary=raw.get("context_summary", "")
                    )
            except Exception as e:
                print(f"Error loading session {self.session_id}: {e}")
                import datetime
                return SessionData(
                    session_id=self.session_id,
                    created_at=datetime.datetime.now().isoformat(),
                    last_interaction=datetime.datetime.now().isoformat()
                )
        else:
            import datetime
            return SessionData(
                session_id=self.session_id,
                created_at=datetime.datetime.now().isoformat(),
                last_interaction=datetime.datetime.now().isoformat()
            )

    def set_email(self, email: str):
        """Associates an email with the session."""
        self.data.email = email
        self.save()

    def set_tier(self, tier: str):
        """Updates the tier (e.g. to premium)."""
        self.data.tier = tier
        self.save()

    def save(self):
        """Persists current state to JSON."""
        try:
            import datetime
            self.data.last_interaction = datetime.datetime.now().isoformat()
            
            with open(self.file_path, 'w', encoding='utf-8') as f:
                # Convert dataclass to dict using asdict
                json.dump(asdict(self.data), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving session {self.session_id}: {e}")

    def add_interaction(self, role: str, content: str, intent: str = None):
        """Adds a message and triggers learning."""
        interaction = Interaction(
            timestamp=time.time(),
            role=role,
            content=content,
            intent=intent
        )
        self.data.interactions.append(interaction)
        
        # Only learn from user messages
        if role == "user":
            self._learn_from_message(content)
            
        self.save()

    def _learn_from_message(self, content: str):
        """Simple rule-based NLP to extract preferences."""
        content = content.lower()
        
        # Food Preferences
        if "vegano" in content or "vegana" in content:
            if "vegan" not in self.data.preferences.food_types:
                self.data.preferences.food_types.append("vegan")
        if "vegetariano" in content:
            if "vegetarian" not in self.data.preferences.food_types:
                self.data.preferences.food_types.append("vegetarian")
        if "carne" in content and "no" not in content: # Risky heuristic
             if "meat" not in self.data.preferences.food_types:
                self.data.preferences.food_types.append("meat")

        # Interests
        interests_map = {
            "arte": "art", "museo": "art", "historia": "history", 
            "antiguo": "history", "jazz": "music", "música": "music",
            "fiesta": "nightlife", "copas": "nightlife", "playa": "beach"
        }
        for kw, val in interests_map.items():
            if kw in content and val not in self.data.preferences.interests:
                self.data.preferences.interests.append(val)

        # Trip Type
        if "niños" in content or "familia" in content:
            self.data.preferences.trip_type = "family"
        elif "pareja" in content or "novio" in content or "novia" in content:
            self.data.preferences.trip_type = "couple"
        elif "amigos" in content or "grupo" in content:
            self.data.preferences.trip_type = "group"
            
        # Price
        if "barato" in content or "económico" in content:
            self.data.preferences.price_range = "low"
        elif "lujo" in content or "caro" in content:
            self.data.preferences.price_range = "high"

    def update_place_status(self, place_name: str, status: str):
        """Updates status of a place (recommended, visited, rejected)."""
        self.data.places_discussed[place_name] = PlaceStatus(
            status=status,
            timestamp=time.time()
        )
        self.save()

    def get_llm_context(self) -> str:
        """Builds a concise context string for the LLM."""
        p = self.data.preferences
        
        # Profile Section
        profile = f"""[PERFIL]
- Viaje: {p.trip_type}
- Precio: {p.price_range}
- Intereses: {', '.join(p.interests) if p.interests else 'Aún no definidos'}
- Comida: {', '.join(p.food_types) if p.food_types else 'Sin restricciones'}"""

        # History Section (Last 5 turns to save tokens)
        history = "[HISTORIAL RECIENTE]"
        recent = self.data.interactions[-5:] 
        for i in recent:
            history += f"\n{i.role.capitalize()}: {i.content[:100]}..." # Truncate long msgs

        # Places Section
        places = "[LUGARES MENCIONADOS]"
        if self.data.places_discussed:
            for name, status in self.data.places_discussed.items():
                places += f"\n- {name} ({status.status})"
        else:
            places += "\n(Ninguno aún)"

        return f"{profile}\n\n{places}\n\n{history}"
        
    def delete_session(self):
        """GDPR: Deletes the session file."""
        if os.path.exists(self.file_path):
            os.remove(self.file_path)

def get_tourist_memory(session_id: str) -> TouristMemory:
    return TouristMemory(session_id)
