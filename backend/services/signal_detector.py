import re
from backend.services.conversation_state import ConversationState

# Regex patterns for rapid detection
PATTERNS = {
    "asked_for_bill": [
        r"\bcuenta\b", r"\bpagar\b", r"\bcobrar\b", r"\bcu(á|a)nto es\b", r"\bdolorosa\b"
    ],
    "mentioned_hurry": [
        r"\bprisa\b", r"\br(á|a)pido\b", r"\birnos\b", r"\btiempo\b"
    ],
    "mentioned_celebration": [
        r"\bcumplea(ñ|n)os\b", r"\baniversario\b", r"\bcelebrar\b", r"\bespecial\b"
    ],
    "dietary_vegetarian": [
        r"\bvegetariano\b", r"\bcarne\b", r"\bvegano\b"
    ],
    "budget_sensitive": [
        r"\bbarato\b", r"\becon(ó|o)mico\b", r"\bprecio\b", r"\bcuesta\b"
    ],
    "wants_recommendation": [
        r"\brecomienda(s|n)\b", r"\bsugiere(s|n)\b", r"\bbueno\b", r"\bespecialidad\b"
    ],
    "praise": [
        r"\bbuen(í|i)simo\b", r"\bincre(í|i)ble\b", r"\bdelicioso\b", r"\bespectacular\b"
    ],
    "complaint": [
        r"\bfr(í|i)o\b", r"\btarda\b", r"\bmal\b", r"\bfe(o|a)\b"
    ]
}

def detect_signals(text: str, state: ConversationState) -> ConversationState:
    """
    Analyzes user input text and updates the state signals.
    """
    if not text:
        return state
        
    text_lower = text.lower()
    
    # helper for regex check
    def check(key):
        return any(re.search(p, text_lower) for p in PATTERNS[key])

    if check("asked_for_bill"):
        state.signals.asked_for_bill = True
        state.phase = "bill" # Force phase transition
        
    if check("mentioned_hurry"):
        state.signals.mentioned_hurry = True
        state.preferences.pace = "quick"
        
    if check("mentioned_celebration"):
        state.signals.mentioned_celebration = True
        
    if check("budget_sensitive"):
        state.preferences.budget_sensitivity = "high"
        
    if check("wants_recommendation"):
        state.signals.asked_for_recommendations = True
        
    if check("praise"):
        state.signals.praised_food = True
        
    if check("complaint"):
        state.signals.complained = True
        
    return state
