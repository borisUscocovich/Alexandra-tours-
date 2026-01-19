from typing import Optional, Dict
from datetime import datetime
from backend.services.conversation_state import ConversationState, OrderItem

class FlowHint(Dict):
    """
    Structured hint for the LLM
    """
    action: str
    suggestion: Optional[str]
    urgency: str # low, medium, high
    can_skip: bool

def get_flow_suggestion(state: ConversationState, weather_temp: float = 20, time_hour: int = 14) -> dict:
    """
    Determines the best next action/suggestion for the waiter based on state.
    """
    
    # 0. Global Overrides
    if state.signals.asked_for_bill or state.phase == "bill":
        return {
            "action": "process_bill",
            "suggestion": "Aquí tenéis la cuenta. ¿Os cobro con tarjeta?",
            "urgency": "high",
            "can_skip": False
        }

    if state.signals.mentioned_hurry:
        return {
            "action": "be_quick",
            "suggestion": None,
            "urgency": "high", 
            "can_skip": True
        }

    # 1. Phase-Based Logic
    
    # --- GREETING -> DRINKS ---
    if state.phase == "greeting":
        # Usually LLM handles greeting, but we can suggest recommending drinks
        return {
            "action": "suggest_drinks",
            "suggestion": "Para empezar, ¿os traigo algo fresquito mientras miráis? Tenemos Cruzcampo de barril muy fría.",
            "urgency": "medium",
            "can_skip": False
        }

    # --- DRINKS -> TAPAS ---
    if state.phase == "drinks":
        # If they have been in drinks phase for > 5 mins without ordering food
        has_food = len(state.order.tapas) > 0 or len(state.order.mains) > 0
        if not has_food and state.time_in_phase_minutes > 5:
            return {
                "action": "suggest_tapas",
                "suggestion": "¿Queréis algo para picar? Las bravas vuelan hoy.",
                "urgency": "low",
                "can_skip": True
            }

    # --- TAPAS -> MAINS ---
    if state.phase == "tapas":
        # If they ordered tapas, maybe suggest mains after a while
        if state.time_in_phase_minutes > 15 and len(state.order.mains) == 0:
             return {
                "action": "suggest_mains",
                "suggestion": "¿Vémos algo más contundente? El solomillo al whisky es especialidad.",
                "urgency": "low",
                "can_skip": True
            }

    # --- CHECK (Eating mains) -> DESSERT ---
    if state.phase == "check" and state.time_in_phase_minutes > 20:
        return {
             "action": "suggest_dessert",
             "suggestion": "¿Habéis dejado hueco para el postre? La tarta de queso es casera.",
             "urgency": "low",
             "can_skip": True
        }

    # 2. Context-Based Upselling (The "Waiter Intuition")
    
    # Wine Pairing
    has_meat = any(i.item.lower() in ["entrecot", "solomillo", "secreto", "presa"] for i in state.order.mains)
    has_wine = any("vino" in i.item.lower() or "rioja" in i.item.lower() for i in state.order.drinks)
    
    if has_meat and not has_wine and state.phase in ["tapas", "mains"]:
        return {
            "action": "upsell_wine",
            "suggestion": "¿Os apetece un Ribera para acompañar esa carne? Tenemos uno por copas muy bueno.",
            "urgency": "medium",
            "can_skip": True
        }

    # Weather
    if weather_temp > 28 and state.phase == "greeting":
         return {
            "action": "weather_drink",
            "suggestion": "Hace un calor terrible fuera. ¿Un tinto de verano bien frío?",
            "urgency": "medium",
            "can_skip": False
        }
        
    if weather_temp < 15 and state.phase in ["greeting", "drinks"]:
         return {
            "action": "weather_food",
            "suggestion": "Con este frío entra genial el guiso del día (Carrillada).",
            "urgency": "medium",
            "can_skip": True
        }

    # Default: Listen
    return {
        "action": "listen",
        "suggestion": None,
        "urgency": "none",
        "can_skip": True
    }
