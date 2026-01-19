from datetime import datetime
import locale
from backend.services.weather import weather_service

# Set locale for spanish day names if possible, else fallback
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except:
    pass # Windows might need different locale string or english fallback is fine for now

class ContextService:
    async def get_dynamic_context(self, city: str = "Barcelona") -> str:
        """
        Returns a natural language string with time, date and weather.
        Example: "Es jueves, son las 14:30 y hace 20°C con cielo despejado en Barcelona."
        """
        now = datetime.now()
        
        # Time and Date
        time_str = now.strftime("%H:%M")
        # Simple translation for days to avoid locale issues on some OS
        days = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
        day_str = days[now.weekday()]
        
        # Weather
        weather = await weather_service.get_weather(city)
        
        context = (
            f"Hoy es {day_str}, son las {time_str}. "
            f"En {weather['city']} hace {weather['temp']}°C y {weather['description']}."
        )
        return context

context_service = ContextService()
