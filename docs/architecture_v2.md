# ARQUITECTURA v2: Alexandra Tours

> Actualizado Enero 2026 - Incluye modelo freemium persistente y sistema de contador

---

## 1. Arquitectura General

```mermaid
flowchart TB
    subgraph Client [Cliente]
        PWA(PWA Mobile/Desktop)
        Voice(ElevenLabs Voice Widget)
    end

    subgraph ElevenLabs [ElevenLabs Cloud]
        ASR(Speech-to-Text)
        LLM(Claude Sonnet)
        TTS(Text-to-Speech)
    end

    subgraph Backend [Backend FastAPI - Render]
        Router(API Router)
        Auth(Session Manager)
        Counter(Usage Counter)
        Cache(Smart Cache)
        Optimizer(Token Optimizer)
        RateLimiter(Rate Limiter)
    end

    subgraph Data [Data Layer]
        JSON[(barcelona_places.json)]
        Sessions[(User Sessions)]
        UsageLog[(Usage Log)]
    end

    subgraph External [APIs Externas]
        Weather(OpenWeather)
        Maps(Google Maps - futuro)
        TripAdvisor(TripAdvisor - futuro)
    end

    PWA <--> Voice
    Voice <--> ASR
    ASR <--> LLM
    LLM <--> TTS
    TTS <--> Voice

    LLM -- "Tool Call" --> Router
    Router --> Auth
    Router --> Counter
    Router --> Cache
    Router --> Optimizer
    Router --> RateLimiter

    Auth --> Sessions
    Counter --> UsageLog
    Cache --> JSON
    Router --> External
```

---

## 2. Flujo de Usuario Completo

```mermaid
flowchart LR
    subgraph Entry [Entrada]
        QR(QR/NFC Scan)
        Direct(URL Directa)
    end

    subgraph Session [Sesión]
        NewUser{Usuario Nuevo?}
        Returning{Usuario Conocido?}
        SessionID(Generar/Recuperar SessionID)
    end

    subgraph Tier [Tier Check]
        CheckTier{Tier?}
        Free(FREE: Acompañamiento básico)
        Premium(PREMIUM: Acompañamiento extendido)
    end

    subgraph Interaction [Interacción]
        Query(Usuario Habla)
        Process(Procesar + Contar)
        Response(Alexandra Responde)
    end

    QR --> NewUser
    Direct --> NewUser
    NewUser -- "Sí" --> SessionID
    NewUser -- "No" --> Returning
    Returning --> SessionID

    SessionID --> CheckTier
    CheckTier -- "Free" --> Free
    CheckTier -- "Premium" --> Premium

    Free --> Query
    Premium --> Query
    Query --> Process
    Process --> Response
    Response --> Query
```

---

## 3. Flujo de Sesión y Autenticación (NUEVO)

**Filosofía: "Primero utilidad, luego identidad"**

```mermaid
flowchart TD
    subgraph Entry [Entrada - 0 Fricción]
        Open([Usuario Abre Web])
        CheckLocal{localStorage tiene sessionID?}
    end

    subgraph Anonymous [Fase Anónima - FREE]
        GenID[Generar UUID sessionID]
        SaveLocal[Guardar en localStorage]
        UseAnon[Usar Alexandra FREE]
        Memory1[(Memoria en backend/data/sessions/)]
    end

    subgraph Trigger [Trigger de Login]
        Limit{Límite FREE alcanzado?}
        WantsMore{Usuario quiere continuar?}
    end

    subgraph Auth [Autenticación - Solo Premium]
        StripeCheckout[Stripe Checkout]
        GetEmail[Stripe devuelve email]
        LinkSession[Asociar sessionID → email]
        Premium[Usuario PREMIUM]
        Memory2[(Memoria persistente cross-device)]
    end

    subgraph Return [Retorno Cross-Device]
        NewDevice([Nuevo Dispositivo])
        EnterEmail[Ingresa email]
        MagicLink[Magic Link / Código]
        RecoverSession[Recuperar sesión + memoria]
    end

    Open --> CheckLocal
    CheckLocal -- "No" --> GenID
    CheckLocal -- "Sí" --> UseAnon
    GenID --> SaveLocal
    SaveLocal --> UseAnon
    UseAnon --> Memory1
    UseAnon --> Limit

    Limit -- "No" --> UseAnon
    Limit -- "Sí" --> WantsMore
    WantsMore -- "No (mañana)" --> UseAnon
    WantsMore -- "Sí (upgrade)" --> StripeCheckout

    StripeCheckout --> GetEmail
    GetEmail --> LinkSession
    LinkSession --> Premium
    Premium --> Memory2

    NewDevice --> EnterEmail
    EnterEmail --> MagicLink
    MagicLink --> RecoverSession
    RecoverSession --> Premium

    style Anonymous fill:#90EE90
    style Auth fill:#FFD700
    style Return fill:#87CEEB
```

### Resumen del Flujo

| Fase | Autenticación | Memoria | Fricción |
|------|---------------|---------|----------|
| **FREE** | Ninguna (localStorage) | Solo ese dispositivo | 0 |
| **PREMIUM** | Email vía Stripe | Cross-device | Mínima (ya paga) |
| **RETORNO** | Magic link a email | Recupera todo | Baja |

### Implementación

**Frontend (localStorage):**
```javascript
// Al cargar la app
let sessionId = localStorage.getItem('alexandra_session');
if (!sessionId) {
    sessionId = crypto.randomUUID();
    localStorage.setItem('alexandra_session', sessionId);
}
// Usar sessionId en todas las llamadas API
```

**Backend (asociar email en upgrade):**
```python
@router.post("/api/upgrade/complete")
async def complete_upgrade(session_id: str, stripe_session: str):
    # Stripe devuelve email del cliente
    customer_email = get_stripe_customer_email(stripe_session)

    # Asociar sessionID con email
    session = load_session(session_id)
    session.email = customer_email
    session.tier = "premium"
    save_session(session)

    # Crear índice email → session_id para recuperación
    save_email_index(customer_email, session_id)
```

**Recuperación cross-device:**
```python
@router.post("/api/session/recover")
async def recover_session(email: str):
    # Buscar session por email
    session_id = get_session_by_email(email)
    if session_id:
        # Enviar magic link o código
        send_magic_link(email, session_id)
        return {"status": "link_sent"}
    return {"status": "not_found"}
```

---

## 4. Sistema de Contador Acumulativo

```mermaid
flowchart TD
    subgraph Interaction [Cada Interacción]
        Msg(Mensaje Usuario)
        Cost(Calcular Costo: ~0.02€)
        Add(Sumar a Contador Sesión)
    end

    subgraph Accumulator [Acumulador]
        Total(Total Acumulado)
        Check{Total > Threshold?}
    end

    subgraph Thresholds [Umbrales]
        T1(Free Limit: 1€ equiv)
        T2(Soft Limit: 3€)
        T3(Hard Limit: 5€)
    end

    subgraph Actions [Acciones]
        Continue(Continuar Normal)
        Nudge(Nudge Suave)
        Upsell(Pantalla Upgrade)
        Pause(Pausa hasta Pago)
    end

    Msg --> Cost
    Cost --> Add
    Add --> Total
    Total --> Check

    Check -- "< T1" --> Continue
    Check -- "T1-T2" --> Nudge
    Check -- "T2-T3" --> Upsell
    Check -- "> T3" --> Pause

    style T1 fill:#90EE90
    style T2 fill:#FFD700
    style T3 fill:#FF6B6B
```

---

## 4. Modelo de Monetización (Stripe)

```mermaid
flowchart TD
    subgraph FreeTier [Free Tier]
        FreeUse(Uso Básico)
        FreeLimit(Hasta ~50 interacciones equiv)
        NoCard(Sin tarjeta requerida)
    end

    subgraph Upgrade [Proceso Upgrade]
        Trigger(Usuario quiere más)
        Card(Ingresa Tarjeta)
        Hold(Stripe Hold: 5€)
        Confirm(Confirmación)
    end

    subgraph PremiumTier [Premium Tier]
        Unlimited(Uso Extendido)
        Counter(Contador Activo)
        Accumulate(Acumula Costos Reales)
    end

    subgraph Billing [Facturación]
        Period(Fin de Período: 7 días)
        Calculate(Calcular Total Real)
        Charge(Cobrar Solo Lo Usado)
        Release(Liberar Diferencia del Hold)
    end

    FreeUse --> FreeLimit
    FreeLimit -- "Límite alcanzado" --> Trigger
    Trigger --> Card
    Card --> Hold
    Hold --> Confirm
    Confirm --> Unlimited

    Unlimited --> Counter
    Counter --> Accumulate
    Accumulate --> Period
    Period --> Calculate
    Calculate --> Charge
    Charge --> Release
```

**Ejemplo:**
- Stripe retiene 10€
- Usuario consume 3.20€ en 7 días
- Se cobra 3.20€, se liberan 6.80€

**Por qué 10€:** Cubre hasta ~500 interacciones/semana (uso extremo). Turista en Barcelona gasta 100-300€/día, 10€ es imperceptible.

---

## 5. Stack por Capas

```mermaid
graph TD
    subgraph Presentation [Presentación]
        PWA(PWA HTML/CSS/JS)
        ThreeJS(Three.js Visualizer)
    end

    subgraph Voice [Voz]
        ElevenLabs(ElevenLabs Conv. AI)
    end

    subgraph Intelligence [Inteligencia]
        Claude(Claude Sonnet 4)
    end

    subgraph API [API Layer]
        FastAPI(FastAPI Python)
    end

    subgraph Services [Servicios]
        Cache(SmartCache)
        RateLimiter(Rate Limiter)
        Metrics(Metrics Dashboard)
        Optimizer(Token Optimizer)
        UsageCounter(Usage Counter)
    end

    subgraph Data [Datos]
        JSON(JSON Files)
        Future[(PostgreSQL - Futuro)]
    end

    subgraph Payments [Pagos - Futuro]
        Stripe(Stripe)
        Lightning(Lightning Network)
    end

    Presentation --> Voice
    Voice --> Intelligence
    Intelligence --> API
    API --> Services
    Services --> Data
    API -.-> Payments

    style Payments fill:#FFD700,stroke:#333
    style UsageCounter fill:#90EE90,stroke:#333
```

---

## 6. Flujo de Optimización de Tokens

```mermaid
flowchart TD
    Query(Query Usuario) --> Optimizer{Optimizer}

    Optimizer -- "Clasificar Intent" --> Intent{Tipo?}

    Intent -- "Simple: Hola, Sí, Gracias" --> Bypass[Bypass LLM]
    Intent -- "Complejo" --> CacheCheck{Cache?}

    CacheCheck -- "Hit" --> CachedResponse[Respuesta Cacheada]
    CacheCheck -- "Miss" --> LazyLoad[Lazy Load Context]

    LazyLoad --> MinimalData[Datos Mínimos]
    MinimalData --> LLM[Generar con LLM]
    LLM --> SaveCache[Guardar en Cache]
    SaveCache --> Response

    Bypass --> Response(Respuesta)
    CachedResponse --> Response

    subgraph Savings [Ahorro de Tokens]
        Bypass
        CachedResponse
        MinimalData
    end

    style Savings fill:#d4af37,stroke:#333
```

---

## 7. Endpoints Principales

| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `/api/tools/city_context` | POST | Tool principal para ElevenLabs |
| `/api/session` | GET | Obtener/crear sesión |
| `/api/usage` | GET | Consultar uso acumulado |
| `/api/upgrade` | POST | Iniciar proceso upgrade |
| `/health` | GET | Health check |

---

## 8. Variables de Entorno

```env
# ElevenLabs
ELEVENLABS_API_KEY=xxx
ELEVENLABS_AGENT_ID=xxx

# OpenWeather
OPENWEATHER_API_KEY=xxx

# Stripe (Futuro)
STRIPE_SECRET_KEY=xxx
STRIPE_WEBHOOK_SECRET=xxx

# Config
ENVIRONMENT=production
FREE_TIER_LIMIT=50
PREMIUM_HOLD_AMOUNT=500  # céntimos
BILLING_PERIOD_DAYS=7
```

---

## 9. Decisiones de Arquitectura

| Decisión | Razón |
|----------|-------|
| Freemium persistente | Evita presión artificial, construye confianza |
| Contador acumulativo | Permite microtransacciones sin comisiones por mensaje |
| Stripe hold | Usuario no siente "cada mensaje cuesta", paga al final |
| Cache agresivo | Reduce costos LLM 40-60% |
| Token optimizer | Bypass para intents simples |

---

## 10. Futuras Integraciones

```mermaid
flowchart LR
    subgraph Current [Actual]
        Weather(OpenWeather)
        JSON(Barcelona Places)
    end

    subgraph Phase2 [Fase 2]
        Maps(Google Maps)
        Places(Google Places)
    end

    subgraph Phase3 [Fase 3]
        TripAdvisor(TripAdvisor)
        Yelp(Yelp)
    end

    subgraph Phase4 [Fase 4]
        Lightning(Lightning Network)
        Nostr(Nostr Identity)
    end

    Current --> Phase2
    Phase2 --> Phase3
    Phase3 --> Phase4
```
