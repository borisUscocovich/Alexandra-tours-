import json
import os
from fastapi import APIRouter, HTTPException, Request
from backend.services.weather import weather_service

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
    import datetime
    from backend.services.weather import weather_service

    try:
        body = await request.json()
    except:
        body = {}

    # Obtener ubicación (default Barcelona centro)
    lat = body.get("latitude", 41.3851)
    lon = body.get("longitude", 2.1734)
    city = body.get("city", "Barcelona")

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

    # 3. Lugares destacados (mock por ahora, luego Google Places API)
    # Load from the new JSON file we created
    import json
    import os
    PLACES_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "barcelona_places.json")
    
    featured_places = []
    if os.path.exists(PLACES_FILE):
        try:
            with open(PLACES_FILE, "r", encoding="utf-8") as f:
                places_data = json.load(f)
                # Just take one from each category for the "featured" list
                p_list = places_data.get("places", {})
                if "restaurants" in p_list and p_list["restaurants"]:
                     r = p_list["restaurants"][0]
                     featured_places.append({
                         "name": r["name"],
                         "type": r["type"], 
                         "distance": "5 min caminando", # Mock distance
                         "tip": r.get("tip", ""),
                         "affiliate_link": r.get("affiliate", {}).get("id")
                     })
                if "attractions" in p_list and p_list["attractions"]:
                     a = p_list["attractions"][0]
                     featured_places.append({
                         "name": a["name"],
                         "type": a["type"],
                         "distance": "20 min transporte",
                         "tip": a.get("tip", ""),
                         "affiliate_link": None
                     })
        except Exception as e:
            print(f"Error loading places: {e}")

    # Fallback if empty or file issue
    if not featured_places:
        featured_places = [
            {
                "name": "Bar Cañete",
                "type": "tapas",
                "distance": "5 min caminando",
                "tip": "Pedir la tortilla y las croquetas",
                "affiliate_link": None
            }
        ]

    # 4. Eventos hoy (mock, luego Eventbrite/Fever API)
    events_today = [
        {
            "name": "Concierto Jazz en Jamboree",
            "time": "21:00",
            "price": "€15",
            "booking_link": "https://example.com"
        }
    ]

    return {
        "city": city,
        "current_time": now.strftime("%H:%M"),
        "time_context": time_context,
        "meal_suggestion": meal_suggestion,
        "weather": weather,
        "featured_places": featured_places,
        "events_today": events_today,
        "instructions": f"Es {time_context} en {city}. El clima es {weather.get('description', 'agradable')}. Sugiere actividades apropiadas para este momento. Si el usuario pregunta por comida, es buen momento para {meal_suggestion}."
    }
