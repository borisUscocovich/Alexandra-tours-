# import chromadb (Removed for ARM64 compatibility)
from backend.core.config import get_settings

settings = get_settings()

class RAGSystem:
    def __init__(self):
        # Replaced heavy ChromaDB with lightweight in-memory store for MVP/ARM64
        self.stories = []
        self._initialize_data()

    def _initialize_data(self):
        """Ingest the 3 hardcoded pilot stories."""
        self.stories = [
            {
                "id": "el_tigre_gracia",
                "text": "Bar familiar desde 1952. El abuelo Paco lo abrió tras volver de Argentina. La especialidad son las patatas bravas con receta secreta de la abuela Rosa. En los 80s era punto de encuentro de músicos del barrio.",
                "metadata": {"local_id": "el_tigre_gracia", "name": "Bar El Tigre"}
            },
            {
                "id": "ca_la_maria_born",
                "text": "Antigua carbonería convertida en restaurante en 1998. Los arcos de piedra son originales del siglo XVIII. Famoso por el arroz negro que solo se hace los jueves.",
                "metadata": {"local_id": "ca_la_maria_born", "name": "Ca la Maria"}
            },
            {
                "id": "el_rincon_barceloneta",
                "text": "Fundado por pescadores en 1923. Las fotos en la pared son de clientes históricos. Hemingway supuestamente comió aquí en 1959, aunque no hay prueba. Mejor momento: atardecer con vista al mar.",
                "metadata": {"local_id": "el_rincon_barceloneta", "name": "El Rincón"}
            }
        ]

    def query(self, local_id: str, query_text: str, n_results: int = 1):
        """Retrieve relevant context for a specific local_id (Simple substring implementation)."""
        # Simple extraction for MVP: Just return the story if local_id matches
        # In a real vector DB we would use embeddings.
        
        matches = [s["text"] for s in self.stories if s["metadata"]["local_id"] == local_id]
        
        if matches:
            return matches[0]
        return None

# Global instance
rag = RAGSystem()

def get_rag():
    return rag
