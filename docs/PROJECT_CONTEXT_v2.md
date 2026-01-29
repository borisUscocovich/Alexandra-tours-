# PROJECT CONTEXT v2: Alexandra Tours

> Documento para compartir con LLMs (ChatGPT, Claude, Antigravity) - Actualizado Enero 2026

---

## 1. Qué ES Alexandra

Alexandra NO es un chatbot genérico. NO es una herramienta de reservas.

Alexandra es una **compañera contextual** diseñada para traducir la ciudad en experiencia vivida. Su valor viene de:
- **Continuidad** - Te recuerda, aprende de ti
- **Memoria** - Sabe lo que te gustó ayer
- **Timing** - Sugiere en el momento correcto, no bombardea

**Frase clave:** "Designed to be remembered, not consumed."

---

## 2. Filosofía de Producto

El producto está construido alrededor de **presencia, no uso**. Alexandra se siente disponible sin ser infinita. Sabe cuándo guiar profundamente y cuándo retirarse.

Este balance preserva:
- Confianza del usuario
- Sostenibilidad operacional (costos de API)

---

## 3. Modelo Freemium (CRÍTICO)

### Lo que SÍ es:
- **Persistente** - NO se reinicia diariamente
- **Con memoria** - Usuarios free pueden volver, ser reconocidos, sentir continuidad
- **Sin presión artificial** - No hay ciclos forzados ni countdowns agresivos

### Lo que NO es:
- ❌ 50 requests/día que se reinician a medianoche
- ❌ Paywall agresivo tras X mensajes
- ❌ Features bloqueadas artificialmente

### La distinción Free vs Premium:
- **Free**: Acompañamiento básico, respuestas concisas, sin profundidad sostenida
- **Premium**: Continuidad extendida, itinerarios detallados, acompañamiento durante toda la estancia

**La diferencia es experiencial, no funcional.**

---

## 4. Por Qué Existe el Pago

El pago existe para permitir que Alexandra **permanezca atenta en el tiempo** sin interrupciones.

NO es:
- Un peaje para desbloquear features
- Una barrera de acceso

SÍ es:
- Una confirmación de que la relación puede profundizarse
- Sin ansiedad de costos
- Sin pausas forzadas

---

## 5. Journey del Usuario

```
[Descubrimiento] → Alexandra ayuda con algo puntual
       ↓
[Utilidad] → Usuario ve valor, vuelve
       ↓
[Confianza] → Alexandra recuerda, personaliza
       ↓
[Compromiso opcional] → Usuario decide profundizar (pago)
       ↓
[Compañera de viaje] → Acompañamiento durante toda la estancia
```

**En ningún momento el sistema debe sentirse extractivo o pushy.**

---

## 6. Stack Técnico (Resumen)

| Capa | Tecnología |
|------|------------|
| Frontend | HTML5/CSS3/JS + Three.js (PWA) |
| Voice AI | ElevenLabs Conversational AI |
| LLM | Claude 3.5/4 Sonnet (via ElevenLabs) |
| Backend | FastAPI (Python 3.11) |
| Hosting | Render (backend) + Netlify (frontend) |
| Data | JSON local → PostgreSQL (futuro) |

---

## 7. URLs Actuales

- **Backend**: `https://alexandra-tours-.onrender.com/docs`
- **Frontend**: `https://alexandra-tours-.onrender.com/`
- **Dominio objetivo**: `alexandra.tours`

---

## 8. Estructura de Carpetas

```
C:\Proyectos\Restaurante red\
├── backend/
│   ├── api/routes.py          # Endpoint principal: /tools/city_context
│   ├── services/
│   │   ├── cache.py           # SmartCache con TTL
│   │   ├── rate_limiter.py    # Por tier (free/premium)
│   │   ├── metrics.py         # Dashboard costos
│   │   ├── optimizer.py       # Ahorro de tokens
│   │   └── weather.py         # OpenWeather API
│   └── data/barcelona_places.json
├── frontend/
│   └── index.html             # Voice Console + Three.js
└── docs/                      # Esta carpeta
```

---

## 9. Estado Actual

**MVP V1.0 - Blindado** (sistema de ahorro de tokens activo)

- ✅ Guía turística funcional
- ✅ Interfaz de voz con visualizador
- ✅ Cache + Rate Limiting + Optimizador
- ✅ Desplegado en Render

---

## 10. Próximos Pasos

1. **Monetización** - Sistema de contador acumulativo + Stripe
2. **Personalidad** - Refinar prompt de Alexandra en ElevenLabs
3. **Base de Datos** - Migrar JSON → PostgreSQL
4. **Autenticación** - Login persistente (sessionID → cuenta real)

---

## 11. Visión a Largo Plazo

Esta estructura permite que Alexandra evolucione hacia:
- Viajes más largos
- Visitantes recurrentes
- Personalización profunda

**Sin cambiar su tono ni traicionar la confianza inicial.**

---

## Resumen Ejecutivo

> Alexandra está diseñada para ser recordada, no consumida. Las decisiones técnicas y de negocio sirven a ese único objetivo.
