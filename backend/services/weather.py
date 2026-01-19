import os
import httpx
from typing import Dict, Any
from datetime import datetime

class WeatherService:
    def __init__(self):
        self.api_key = os.getenv("OPENWEATHER_API_KEY")
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"

    def _get_mock_weather(self, city: str) -> Dict[str, Any]:
        """
        Returns realistic mock weather based on time of day.
        Makes the demo feel alive without API key.
        """
        hour = datetime.now().hour

        # Morning (6-12): Fresh and sunny
        if 6 <= hour < 12:
            return {
                "city": city,
                "temp": 14,
                "description": "fresco y soleado, buen día para un café",
                "humidity": 65,
                "mock": True
            }
        # Afternoon (12-18): Warm
        elif 12 <= hour < 18:
            return {
                "city": city,
                "temp": 22,
                "description": "agradable y soleado",
                "humidity": 50,
                "mock": True
            }
        # Evening (18-22): Cool
        elif 18 <= hour < 22:
            return {
                "city": city,
                "temp": 17,
                "description": "fresquito, perfecto para una caña",
                "humidity": 60,
                "mock": True
            }
        # Night (22-6): Cold
        else:
            return {
                "city": city,
                "temp": 12,
                "description": "frío, ideal para algo calentito",
                "humidity": 70,
                "mock": True
            }

    async def get_weather(self, city: str = "Barcelona") -> Dict[str, Any]:
        """
        Get current weather for a specific city.
        Returns normalized format: {city, temp, description, humidity}
        """
        if not self.api_key:
            return self._get_mock_weather(city)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.base_url,
                    params={
                        "q": city,
                        "appid": self.api_key,
                        "units": "metric",
                        "lang": "es"
                    }
                )
                response.raise_for_status()
                data = response.json()

                # Normalize to simple format
                return {
                    "city": data.get("name", city),
                    "temp": round(data["main"]["temp"]),
                    "description": data["weather"][0]["description"],
                    "humidity": data["main"]["humidity"],
                    "mock": False
                }
        except Exception as e:
            print(f"Error fetching weather: {e}")
            return self._get_mock_weather(city)

# Singleton instance
weather_service = WeatherService()
