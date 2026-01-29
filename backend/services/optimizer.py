import re
from typing import Dict, Any, Optional, List

class TokenOptimizer:
    """
    Implements token-saving hacks:
    - Intent classification (lightweight)
    - Context pruning/filtering
    - Logic bypass instructions
    """
    
    def __init__(self):
        # Regex patterns for lightweight classification
        self.patterns = {
            "greeting": r"^(hola|hi|hello|buenos|buenas|hey|bonjour|ciao)",
            "confirm": r"^(si|yes|ok|vale|genial|perfecto|sure|yep|da|oui)$",
            "deny": r"^(no|nope|nan|non)$",
            "repeat": r"^(repite|repeat|como|pardon|what)$",
            "gratitude": r"^(gracias|thanks|merci|danke|grazie)"
        }
        
        # Pre-computed responses (Templates) - Multi-language support could be better, 
        # but for hack/MVP we provide simple universal or Spanish defaults (User request implies Spanish base but multilingual support)
        # We will instruct the LLM to translate these if needed or use them raw.
        self.templates = {
            "greeting": "¡Hola! ¿En qué te puedo ayudar hoy? / Hello! How can I help you?",
            "confirm": "Perfecto. / Perfect.",
            "gratitude": "¡De nada! / You're welcome.",
            "repeat": "Repito: {last_response}" 
        }

    def normalize_input(self, text: str) -> str:
        """
        Hack 9: Normaliza input (lowercase, strip, remove hesitation sounds)
        """
        if not text: return ""
        text = text.lower().strip()
        # Remove hesitation sounds (simple list)
        text = re.sub(r"\b(eh|hmm|uh|um|estee|bueno)\b", "", text)
        return re.sub(r"\s+", " ", text).strip()

    def classify_intent(self, text: str) -> str:
        """
        Hack 5: Clasificación ligera Regex
        Updates for V2: distinguish 'medium' vs 'high' cost
        """
        for intent, pattern in self.patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                # These are all "Low Cost" (Cheap) -> Bypass
                return intent
        
        # Heuristic for Medium vs High Cost
        # High Cost keywords: planning, multi-day, comparison, deep history
        high_cost_keywords = ["itinerario", "plan", "ruta", "dias", "comparar", "historia", "diferencia", "mejor opcion", "days", "trip"]
        if any(k in text.lower() for k in high_cost_keywords):
            return "high_cost"
            
        # High Cost by length (long complex questions)
        if len(text.split()) > 15:
            return "high_cost"
            
        # Default to Medium Cost (Simple questions)
        return "medium_cost"

    def get_optimized_response(self, text: str, last_response: str = "") -> Dict[str, Any]:
        """
        Determines if we can bypass the LLM reasoning (Heavy Lifting) 
        and just instruct it to say something simple.
        
        Returns:
            {
                "bypass": bool,
                "instruction": str, # What the LLM should do
                "suggested_response": str # The exact text to say if bypass is True
                "intent": str # Added for tracking
            }
        """
        clean_text = self.normalize_input(text)
        intent = self.classify_intent(clean_text)
        
        # Hack 6: Rules for bypassing complex logic (Low Cost)
        if intent == "greeting":
            return {
                "bypass": True,
                "intent": intent,
                "instruction": "DETECTED_INTENT: Greeting. ACTION: Reply slightly enthusiastically with a short greeting in the user's language. Do NOT ask complex questions yet.",
                "suggested_response": self.templates["greeting"]
            }
            
        if intent == "confirm":
             return {
                "bypass": True,
                "intent": intent,
                "instruction": "DETECTED_INTENT: Confirmation. ACTION: Acknowledge briefly (e.g., 'Great', 'Okay').",
                "suggested_response": self.templates["confirm"]
            }
            
        if intent == "gratitude":
             return {
                "bypass": True,
                "intent": intent,
                "instruction": "DETECTED_INTENT: Gratitude. ACTION: Say 'You're welcome' briefly.",
                "suggested_response": self.templates["gratitude"]
            }

        if intent == "repeat":
             return {
                "bypass": True,
                "intent": intent,
                "instruction": f"DETECTED_INTENT: Request Repeat. ACTION: Repeat the previous information: '{last_response}'",
                "suggested_response": last_response
            }

        # Medium Cost (Simple Query)
        if intent == "medium_cost":
             return {
                "bypass": False,
                "intent": intent,
                "instruction": "DETECTED_INTENT: Simple Query. ACTION: Check Cache first. Reply consistently but concisely (max 2 sentences).",
                "suggested_response": None
            }

        # High Cost (Deep Dive)
        return {
            "bypass": False,
            "intent": "high_cost",
            "instruction": "DETECTED_INTENT: Complex Planning. ACTION: Use full context, memory, and reasoning. Create a personalized answer but keep it structure (max 3-4 sentences).",
            "suggested_response": None
        }

    def filter_context(self, user_query: str, all_places: List[Dict]) -> List[Dict]:
        """
        Hack 3: Contexto Lazy.
        Filtra la lista de lugares basada en keywords del query.
        """
        query = user_query.lower()
        
        # Keywords mapping
        categories = {
            "comida": ["restaurante", "tapas", "food", "eat", "cena", "dinner", "lunch", "hambre"],
            "arte": ["museo", "arte", "museum", "art", "cultura", "history"],
            "aire_libre": ["parque", "playa", "park", "beach", "walk", "caminar"],
            "noche": ["bar", "club", "copas", "drink", "party", "fiesta"]
        }
        
        # Determine relevant categories
        active_categories = []
        for cat, keywords in categories.items():
            if any(k in query for k in keywords):
                active_categories.append(cat)
                
        if not active_categories:
            # Hack 11: Degradación gradual / Default
            # Keep the list short (top 3 mixed)
            return all_places[:3] 
            
        # Filter
        filtered = []
        for p in all_places:
            # This assumes 'type' in place matches our categories or we do fuzzy match
            # For this MVP, we look for matches in the 'type' or 'name' or 'tip' of the place
            p_str = (str(p.get("type")) + str(p.get("name")) + str(p.get("tip"))).lower()
            
            # Check if place matches any active category keyword
            is_match = False
            for cat in active_categories:
                for k in categories[cat]:
                    if k in p_str:
                        is_match = True
                        break
                if is_match: break
            
            if is_match:
                filtered.append(p)
                
        # Hack 1: Limit results to save tokens
        return filtered[:3]

    def get_response_config(self, tier: str = "free") -> dict:
        """Configura respuesta según tier."""

        if tier == "free":
            return {
                "max_places": 3,           # Solo 3 sugerencias
                "max_response_tokens": 100, # Respuestas cortas
                "include_tips": False,      # Sin tips detallados
                "include_booking_links": False,  # Sin affiliate (o sí, para monetizar)
                "include_events": False,    # Sin eventos
                "persona": "concise"        # Personalidad breve
            }
        else:  # premium
            return {
                "max_places": 10,
                "max_response_tokens": 300,
                "include_tips": True,
                "include_booking_links": True,
                "include_events": True,
                "persona": "detailed"
            }

optimizer = TokenOptimizer()
