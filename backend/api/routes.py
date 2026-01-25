import json
import os
from fastapi import APIRouter, HTTPException, Request
from backend.services.weather import weather_service
from backend.services.optimizer import optimizer
from backend.services.cache import cache, CACHE_TTL
from backend.services.rate_limiter import rate_limiter
from backend.services.metrics import metrics
from backend.services.analytics import analytics
from fastapi.responses import HTMLResponse
import datetime
import time
import os

router = APIRouter()

# Path to the data file
DATA_FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "el_tigre.json")

@router.get("/restaurant/{local_id}")
async def get_restaurant_data(local_id: str):
    """
    Get full restaurant data by ID.
    """
    return get_restaurant_data_internal(local_id)

def get_restaurant_data_internal(local_id: str):
    if not os.path.exists(DATA_FILE_PATH):
        raise HTTPException(status_code=500, detail="Restaurant data file not found")
    
    try:
        with open(DATA_FILE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        restaurant = data.get("restaurant")
        if not restaurant:
             raise HTTPException(status_code=404, detail="Restaurant data structure invalid")
             
        if restaurant.get("id") != local_id and local_id != "default":
             # For this mockup, we mostly ignore the ID or support just one
             if local_id != restaurant.get("id"):
                 raise HTTPException(status_code=404, detail=f"Restaurant {local_id} not found")
        
        return restaurant
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error decoding restaurant data")
    except Exception as e:
        print(f"Error loading data: {e}")
        # If calling from internal function, we might want to re-raise or handle differently, 
        # but for now raising HTTPException is fine as it will be caught by FastAPI or caller can catch it.
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/weather/{city}")
async def get_weather(city: str):
    """
    Get current weather for the city.
    """
    return await weather_service.get_weather(city)

@router.post("/conversation/log")
async def log_conversation(request: Request):
    """
    Log conversation data for analysis.
    """
    try:
        body = await request.json()
        # In a real app, save to DB. Here we just print or pass.
        print(f"Conversation Log: {body}")
        return {"status": "logged"}
    except Exception as e:
        print(f"Error logging conversation: {e}")
        return {"status": "error", "detail": str(e)}

@router.post("/tools/context")
async def get_tool_context(request: Request):
    """
    Tool endpoint for ElevenLabs Managed Agent.
    Input: { "conversation_id": "...", "user_message": "..." } OR empty body
    Returns: Full context + State + Flow Hints
    """
    from backend.services.context import context_service
    from backend.services.conversation_state import get_state, update_state, OrderItem
    from backend.services.signal_detector import detect_signals
    from backend.services.flow_logic import get_flow_suggestion

    try:
        # Handle empty body or different formats from ElevenLabs
        try:
            body = await request.json()
        except:
            body = {}

        conversation_id = body.get("conversation_id", body.get("session_id", "default_session"))
        user_message = body.get("user_message", body.get("trigger", ""))
        
        print(f"--- TOOL REQUEST RECEIVED ---")
        print(f"CID: {conversation_id}")
        print(f"MSG: {user_message}")
        
        # 1. Get/Create State
        state = get_state(conversation_id)
        
        # 2. Update State with Signals (NLP)
        state = detect_signals(user_message, state)
        update_state(state) # Save updates
        
        # 3. Get External Context (Weather/Time)
        dynamic_info = await context_service.get_dynamic_context()
        # Parse temp/time for logic (Mocking for now or extracting string)
        # In real impl, context_service should return structured data too
        import datetime
        current_hour = datetime.datetime.now().hour
        # Assume temp is 25 for logic default if not parsed
        temp = 25 

        # 4. Calculate Logic (The "Waiter Brain")
        flow_hint = get_flow_suggestion(state, weather_temp=temp, time_hour=current_hour)
        
        # 5. Get Menu Data
        restaurant_data = get_restaurant_data_internal("default")

        # 6. Construct Guardrails/Instructions
        instructions = (
            f"Fase actual: {state.phase.upper()}. "
            f"Llevan {int(state.time_in_phase_minutes)} min en esta fase. "
            f"Hint del Supervisor: {flow_hint['suggestion'] if flow_hint['suggestion'] else 'Ninguno, fluye natural'}. "
            "Usa 'restaurant_info' para el menú. "
            "Si el cliente pide algo, confirma, pero NO inventes precios. "
            "Si 'flow_hint' sugiere algo, intenta colarlo sutilmente si tiene sentido."
        )

        return {
            "conversation_status": "active",
            "context_dynamic": dynamic_info,
            "conversation_state": state.dict(), # Sends full state (Order, Preferences...)
            "flow_hint": flow_hint,
            "restaurant_info": restaurant_data,
            "instructions": instructions
        }

    except Exception as e:
        print(f"Tool Error: {e}")
        # Fallback to basic context if logic fails
        return {
             "error": str(e),
             "restaurant_info": get_restaurant_data_internal("default"),
             "instructions": "Error en sistema de estado. Actúa como camarera normal básica."
        }



@router.post("/tools/city_context")
async def get_city_context(request: Request):
    """
    Tool endpoint para Alexandra Tours.
    Devuelve contexto urbano: clima, lugares cercanos, eventos, hora local.
    """
    from backend.services.weather import weather_service

    try:
        body = await request.json()
    except:
        body = {}

    # 1. Identificar usuario
    user_id = body.get("session_id", body.get("conversation_id", "anonymous"))
    tier = body.get("tier", "free")
    user_message = body.get("user_message", "")

    # 2. Check rate limit
    limit_check = rate_limiter.check_limit(user_id, tier)
    if not limit_check["allowed"]:
        metrics.record_bypass()
        return {
            "error": "rate_limited",
            "message": limit_check["message"],
            "reset_in": limit_check.get("reset_in"),
            "upgrade_url": "https://alexandra.tours/premium"
        }

    # 3. Check cache
    # Solo usamos cache si NO hay mensaje especifico (contexto general)
    cache_key = f"city_context:{body.get('city', 'Barcelona')}:{tier}"
    cached = cache.get(cache_key)
    if cached and not user_message:
        metrics.cache_hits += 1
        return cached
    
    if not user_message:
         metrics.cache_misses += 1

    # Obtener ubicación (default Barcelona centro)
    lat = body.get("latitude", 41.3851)
    lon = body.get("longitude", 2.1734)
    city = body.get("city", "Barcelona")
    
    # Extract query for optimization
    user_query = body.get("query", body.get("user_message", ""))

    # 1. Clima actual
    weather = await weather_service.get_weather(city)

    # 2. Hora local y contexto temporal
    now = datetime.datetime.now()
    hour = now.hour

    if 6 <= hour < 12:
        time_context = "mañana"
        meal_suggestion = "desayuno o brunch"
    elif 12 <= hour < 17:
        time_context = "mediodía"
        meal_suggestion = "almuerzo"
    elif 17 <= hour < 21:
        time_context = "tarde"
        meal_suggestion = "tapas o aperitivo"
    else:
        time_context = "noche"
        meal_suggestion = "cena o copas"

    # Get Tier Config
    tier_config = optimizer.get_response_config(tier)

    # 3. Lugares destacados (Lazy Context)
    import json
    import os
    PLACES_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "barcelona_places.json")
    
    all_places = []
    if os.path.exists(PLACES_FILE):
        try:
            with open(PLACES_FILE, "r", encoding="utf-8") as f:
                places_data = json.load(f)
                # Flatten the list for filtering
                p_list = places_data.get("places", {})
                for cat, items in p_list.items():
                    for item in items:
                        item['category'] = cat # Add category metadata
                        all_places.append(item)
        except Exception as e:
            print(f"Error loading places: {e}")

    featured_places = []
    
    # Hack 3: Contexto Lazy / Hack 1: Filter
    if user_query:
        featured_places = optimizer.filter_context(user_query, all_places)
    else:
        # Default if no query
        if all_places: featured_places = all_places[:tier_config["max_places"]]

    # Enforce tier limits even on filtered results
    featured_places = featured_places[:tier_config["max_places"]]

    # Fallback
    if not featured_places:
        featured_places = [
            {"name": "Bar Cañete", "type": "tapas", "tip": "Clásico imprescindible.", "distance": "5min"}
        ]

    # 4. Eventos
    if tier_config["include_events"]:
        events_today = [
            {"name": "Jazz en Jamboree", "time": "21:00", "price": "15€"}
        ]
    else:
        events_today = []
    
    # Hacks 5, 6, 7, 9, 15: Optimization Logic
    opt_result = optimizer.get_optimized_response(user_query)
    
    base_instruction = f"Es {time_context} en {city}. Clima: {weather.get('description', 'ok')}. Actividad sugerida: {meal_suggestion}. "
    
    # Brevity Rules
    brevity_rules = (
        " REGLAS DE BREVEDAD (CRÍTICO): "
        "- Máximo 2 oraciones por respuesta "
        "- NO listas largas, máximo 3 opciones "
        "- Usa '¿Quieres que te cuente más?' en vez de explicar todo "
    )
    if tier == "free":
        brevity_rules += "- Si el usuario es FREE tier: respuestas ultra-concisas y NUNCA repitas información. "

    if opt_result["bypass"]:
        # Strong instruction to just follow the script
        final_instructions = f"{opt_result['instruction']} (Responde EXACTAMENTE esto o traducido: '{opt_result['suggested_response']}')"
    else:
        # Complex logic allowed, but keep it short
        final_instructions = f"{base_instruction} {opt_result['instruction']} {brevity_rules}"

    response = {
        "city": city,
        "current_time": now.strftime("%H:%M"),
        "time_context": time_context,
        "meal_suggestion": meal_suggestion,
        "weather": weather,
        "featured_places": featured_places,
        "events_today": events_today,
        "instructions": final_instructions,
        "tier": tier
    }

    # 5. Guardar en cache (Solo si no hay mensaje específico)
    if not user_query:
        cache.set(cache_key, response, CACHE_TTL["city_context"])

    # 6. Registrar request
    rate_limiter.record_request(user_id)
    metrics.record_request(tier)

    # Estimate logic for metrics (approx)
    tokens_in = len(user_message) / 4
    tokens_out = len(str(response)) / 4
    metrics.record_llm_call(int(tokens_in), int(tokens_out))

    # 7. Persistent Analytics Log
    analytics.record_interaction(
        user_id=user_id,
        tier=tier,
        endpoint="city_context",
        tokens_in=int(tokens_in),
        tokens_out=int(tokens_out),
        bypass=opt_result["bypass"],
        intent=opt_result.get("intent", "unknown"), # Optimizer logic normally returns this inside, assuming hack
        city=city
    )

    return response

@router.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard():
    """Serves the static admin dashboard."""
    # En prod idealmente usar Jinja2, aquí leemos el archivo simple
    dash_path = os.path.join(os.path.dirname(__file__), "..", "admin_dashboard.html")
    if os.path.exists(dash_path):
        with open(dash_path, "r", encoding="utf-8") as f:
            return f.read()
    return "Dashboard file not found."

@router.get("/api/admin/stats")
async def get_admin_stats(api_key: str = None):
    """JSON Data for dashboard."""
    return analytics.get_dashboard_stats()

@router.get("/admin/metrics_legacy")
async def get_metrics_legacy(api_key: str = None):
    """Dashboard interno de costos."""
    # TODO: Proteger con API key
    return {
        "usage": metrics.to_dict(),
        "cache": cache.stats(),
        "timestamp": time.time()
    }
