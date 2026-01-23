import httpx
from backend.core.config import get_settings
from typing import List, Dict, Any, Optional

settings = get_settings()

class PlacesService:
    def __init__(self):
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        self.base_url = "https://places.googleapis.com/v1/places:searchText"
        
    async def get_recommendations(self, city: str, context: str = "food", limit: int = 3) -> List[Dict[str, Any]]:
        """
        Get curated recommendations using Google Places API (New).
        Usage: context can be 'tapas', 'jazz', 'dinner', etc.
        """
        if not self.api_key:
            print("⚠️ No Google Maps API Key found. Using mock data.")
            return []

        search_query = f"{context} in {city}"
        
        # Field mask: what data we want back to save cost/latency
        field_mask = "places.id,places.displayName,places.formattedAddress,places.rating,places.userRatingCount,places.priceLevel,places.types,places.location"

        try:
            headers = {
                "Content-Type": "application/json",
                "X-Goog-Api-Key": self.api_key,
                "X-Goog-FieldMask": field_mask
            }
            
            body = {
                "textQuery": search_query,
                "maxResultCount": limit,
                # "minRating": 4.0 # Optional filter logic we could add
                "rankPreference": "RELEVANCE" 
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(self.base_url, json=body, headers=headers, timeout=10.0)
                
                if response.status_code != 200:
                    print(f"Google Places Error: {response.text}")
                    return []

                data = response.json()
                places = data.get("places", [])
                
                results = []
                for p in places:
                    name = p.get("displayName", {}).get("text", "Unknown")
                    rating = p.get("rating", "N/A")
                    count = p.get("userRatingCount", 0)
                    address = p.get("formattedAddress", "")
                    
                    # Estimate distance/tip (Mocking purely dynamic data for now)
                    # content generation from LLM would be ideal here, but we keep it fast
                    
                    price = "€" * len(str(p.get("priceLevel", ""))) if p.get("priceLevel") else "€€"
                    
                    results.append({
                        "name": name,
                        "type": context,
                        "distance": "Calculando...", # Requires Directions API
                        "rating": f"{rating}⭐ ({count})",
                        "price": price,
                        "tip": f"Top rated spot for {context} at {address.split(',')[0]}",
                        "affiliate_link": None # Add affiliate logic later
                    })
                    
                return results

        except Exception as e:
            print(f"Error fetching places: {e}")
            return []

# Singleton
places_service = PlacesService()
