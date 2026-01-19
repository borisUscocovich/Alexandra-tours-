from datetime import datetime
from typing import List, Dict, Optional, Literal, Any
from pydantic import BaseModel, Field

# --- DATA MODELS ---

class OrderItem(BaseModel):
    item: str
    qty: int = 1
    price: float = 0.0

class Order(BaseModel):
    drinks: List[OrderItem] = []
    tapas: List[OrderItem] = []
    mains: List[OrderItem] = []
    desserts: List[OrderItem] = []
    coffee: List[OrderItem] = []
    
    @property
    def total(self) -> float:
        t = 0.0
        for lst in [self.drinks, self.tapas, self.mains, self.desserts, self.coffee]:
            for i in lst: t += i.price * i.qty
        return round(t, 2)
        
    @property
    def summary(self) -> List[str]:
        items = []
        for lst in [self.drinks, self.tapas, self.mains, self.desserts, self.coffee]:
            for i in lst: items.append(f"{i.qty}x {i.item} ({i.price}€)")
        return items

class Preferences(BaseModel):
    dietary: List[str] = []
    allergies: List[str] = []
    spice_tolerance: Literal["low", "medium", "high"] = "medium"
    budget_sensitivity: Literal["low", "normal", "high"] = "normal"
    pace: Literal["quick", "normal", "relaxed"] = "normal"

class Signals(BaseModel):
    asked_for_bill: bool = False
    mentioned_hurry: bool = False
    mentioned_celebration: bool = False
    asked_for_recommendations: bool = False
    complained: bool = False
    praised_food: bool = False

class SuggestionHistory(BaseModel):
    item: str
    accepted: bool
    timestamp: datetime = Field(default_factory=datetime.now)

class ConversationState(BaseModel):
    # Identification
    session_id: str
    table_id: str = "mesa_01"
    started_at: datetime
    last_activity: datetime = Field(default_factory=datetime.now)

    # Phase (greeting, drinks, tapas, mains, check, dessert, coffee, bill, farewell)
    phase: str = "greeting" 
    phase_started_at: datetime = Field(default_factory=datetime.now)
    
    # Order
    order: Order = Field(default_factory=Order)
    
    # Party
    party_size: int = 2
    party_type: Literal["pareja", "amigos", "familia", "negocios", "solo"] = "pareja"
    
    # Intelligence
    preferences: Preferences = Field(default_factory=Preferences)
    signals: Signals = Field(default_factory=Signals)
    suggestions_made: List[SuggestionHistory] = []
    suggestions_rejected_count: int = 0
    
    # Lang
    language: str = "es"

    @property
    def time_in_phase_minutes(self) -> float:
        delta = datetime.now() - self.phase_started_at
        return delta.total_seconds() / 60.0

# --- STORAGE (In-Memory for MVP) ---
_states: Dict[str, ConversationState] = {}

def get_state(session_id: str) -> ConversationState:
    if session_id not in _states:
        # New Session
        print(f"[State] Creating new session state for {session_id}")
        _states[session_id] = ConversationState(
            session_id=session_id,
            started_at=datetime.now()
        )
    return _states[session_id]

def update_state(state: ConversationState):
    state.last_activity = datetime.now()
    _states[state.session_id] = state
    # In production: save_to_redis(state)
