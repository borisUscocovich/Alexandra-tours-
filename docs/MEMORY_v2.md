# MEMORY v2: Sistema de Memoria Persistente

> Especificación para memoria de sesión de turista (NO camarero)
> Enero 2026

---

## 1. Problema Actual

| Componente | Estado Anterior ("Camarero") | Necesidad Actual ("Alexandra") |
|------------|------------------------------|--------------------------------|
| **Modelo** | Fases (Bebida->Comida->Postre) | Exploración libre (Día/Noche) |
| **Persistencia** | Volátil (RAM) | Persistente (JSON/DB) |
| **Identidad** | Anónima por mesa | Persistente por SessionID |
| **Datos** | Pedido actual | Preferencias, historial, alergias |

El modelo anterior `conversation_state.py` estaba optimizado para un flujo lineal de ventas. Alexandra necesita recordar que ayer dijiste que te gustaba el jazz.

---

## 2. Modelo de Datos: `TouristSession`

Estructura JSON que se guardará en `backend/data/sessions/{session_id}.json`.

```json
{
  "session_id": "uuid-v4",
  "created_at": "ISO-8601",
  "last_interaction": "ISO-8601",
  "tier": "free|premium",
  
  "preferences": {
    "food_types": ["tapas", "vegetariano"],
    "interests": ["historia", "jazz"],
    "price_range": "low|medium|high",
    "trip_type": "solo|couple|group|family",
    "language": "es"
  },
  
  "interactions": [
    {
      "timestamp": 1234567890,
      "role": "user|assistant",
      "content": "Me gusta la paella",
      "intent": "preference_update"
    }
  ],
  
  "places_discussed": {
    "bar-canete": {
      "status": "recommended|visited|rejected",
      "timestamp": 1234567890
    }
  },

  "context_summary": "Usuario busca sitios baratos, le gusta el gótico."
}
```

---

## 3. Lógica de Negocio

### 3.1 Detección Automática (Learning)

El sistema debe analizar cada mensaje del usuario buscando keywords para actualizar `preferences` automáticamente.

| Keyword Trigger | Acción | Data Update |
|-----------------|--------|-------------|
| "soy vegano", "no carne" | Add Preference | `food_types.append("vegan")` |
| "me gusta el arte" | Add Interest | `interests.append("art")` |
| "voy con niños" | Set Trip Type | `trip_type = "family"` |
| "algo barato" | Set Price | `price_range = "low"` |

### 3.2 Construcción de Contexto (Retrieval)

Para ahorrar tokens, NO enviamos todo el historial al LLM. Construimos un "System Context" dinámico:

```text
[PERFIL USUARIO]
Intereses: jazz, historia.
Viaje: pareja.
Presupuesto: medio.

[HISTORIAL RECIENTE]
User: ¿Qué hacemos hoy?
Alex: Podríais ir al Born...
User: ¿Hay algo de música?

[LUGARES YA MENCIONADOS]
- Jamboree (recomendado)
```

### 3.3 Gestión de Archivos

- **Path**: `backend/data/sessions/`
- **Formato**: `{session_id}.json`
- **Lazy Loading**: Solo cargar el JSON cuando se recibe request de ese usuario.
- **Auto-Save**: Guardar tras cada actualización de estado.

---

## 4. GDPR / Privacidad

- **Endpoint de borrado**: `DELETE /api/session/{id}` debe eliminar el archivo físico.
- **Retention**: Script cron (futuro) borrará sesiones inactivas > 30 días (Free) o > 1 año (Premium).

---

## 5. Clase Python (`TouristMemory`)

Debe reemplazar a `conversation_state` y `context_service`.

```python
class TouristMemory:
    def __init__(self, session_id):
        self.data = self._load(session_id)
    
    def add_message(self, role, content, intent=None):
        # Add to interactions list
        # Trigger learning logic
        pass
        
    def get_llm_context(self) -> str:
        # Build prompt string
        pass
        
    def _learn_from_message(self, content):
        # NLP simple rules
        pass
```

---

## 6. Prompt para Implementación

Implementa `backend/services/tourist_memory.py` siguiendo estas especificaciones. Asegúrate de manejar la concurrencia de archivos básica (aunque para MVP no necesitamos locks complejos).
