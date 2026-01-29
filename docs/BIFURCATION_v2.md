# BIFURCATION v2: Separación de Productos

> Documento que define la separación entre Alexandra Turismo (B2C) y Camarero IA (B2B)
> Enero 2026

---

## 1. Contexto

El proyecto comenzó como **"Hustler IA - Camarero Inteligente"** para restaurantes (B2B).

Evolucionó a **"Alexandra Tours"** como guía turística (B2C).

**Decisión:** Mantener ambos productos **separados** en código y documentación.

---

## 2. Los Dos Productos

### Producto A: Camarero IA (B2B)

| Aspecto | Valor |
|---------|-------|
| **Nombre** | Hustler IA / Camarero Inteligente |
| **Target** | Restaurantes, bares, hoteles |
| **Modelo** | B2B - Suscripción mensual al local |
| **Interacción** | NFC en mesa → camarero virtual |
| **Flujo** | Drinks → Tapas → Mains → Dessert → Bill |
| **Monetización** | Local paga 99-600€/mes |

### Producto B: Alexandra Tours (B2C)

| Aspecto | Valor |
|---------|-------|
| **Nombre** | Alexandra Tours |
| **Target** | Turistas individuales |
| **Modelo** | B2C - Freemium + Hold semanal |
| **Interacción** | QR/NFC/URL → guía turística |
| **Flujo** | Descubrimiento → Recomendación → Itinerario |
| **Monetización** | Usuario paga por uso real |

---

## 3. Estructura de Carpetas (Bifurcación)

```
C:\Proyectos\
├── Restaurante red\           # Alexandra Tours (B2C) - ACTIVO
│   ├── backend/
│   ├── frontend/
│   ├── docs/
│   │   ├── PROJECT_CONTEXT_v2.md
│   │   ├── architecture_v2.md
│   │   ├── conversation_flow_v2.md  # Flujo TURISTA
│   │   ├── MONETIZATION_v2.md
│   │   └── BIFURCATION_v2.md
│   └── ...
│
└── Camarero-B2B\              # Camarero IA (B2B) - PRESERVADO
    ├── backend/               # Código original sin modificar
    ├── frontend/
    ├── docs/
    │   ├── conversation_flow.md  # Flujo CAMARERO (original)
    │   └── ...
    └── ...
```

---

## 4. Qué Preservar del Camarero B2B

### Código a Mantener Intacto

| Archivo | Razón |
|---------|-------|
| `conversation_flow.md` (v1) | Flujo de camarero: drinks → bill |
| `backend/services/flow_logic.py` | Lógica de fases de servicio |
| `backend/services/signal_detector.py` | Detección NLP (prisa, celebración) |
| `backend/data/el_tigre.json` | Data del restaurante piloto |
| System prompt de ElevenLabs | Personalidad de camarero |

### Lo que NO se comparte

| Camarero B2B | Alexandra B2C |
|--------------|---------------|
| Flujo lineal (drinks→bill) | Flujo libre (exploración) |
| Contexto: menú, precios | Contexto: ciudad, lugares |
| Upsell de platos | Upsell de upgrade premium |
| Sin monetización directa | Freemium + Stripe |
| Cliente = restaurante | Cliente = turista |

---

## 5. Plan de Acción

### Inmediato (Esta semana)

1. **Crear carpeta separada** para Camarero B2B:
   ```powershell
   mkdir C:\Proyectos\Camarero-B2B
   ```

2. **Copiar código original** antes de más cambios:
   ```powershell
   # Copiar estado actual del camarero
   xcopy "C:\Proyectos\Restaurante red\*" "C:\Proyectos\Camarero-B2B\" /E /I
   ```

3. **Preservar docs originales**:
   - `conversation_flow.md` (flujo camarero)
   - `el_tigre.json` (data restaurante)

### En Paralelo

| Producto | Acción |
|----------|--------|
| **Camarero B2B** | Congelar desarrollo, mantener funcional |
| **Alexandra B2C** | Desarrollo activo, implementar monetización |

---

## 6. Cuándo Retomar Camarero B2B

### Triggers para reactivar

- [ ] Alexandra Tours validado (50+ power users)
- [ ] Ingresos estables cubriendo costos
- [ ] Contacto de restaurante interesado
- [ ] Capacidad de manejar dos productos

### Ventaja de tenerlo listo

- Código ya funciona (MVP completado 12 Ene)
- Solo necesita deployment y ventas
- Puede ser fuente de ingresos B2B mientras B2C escala

---

## 7. Diferencias Técnicas Clave

### System Prompt

**Camarero:**
```
Eres el camarero virtual de Bar El Tigre. Conoces la carta,
los precios, las especialidades. Guías al cliente por el
servicio: bebidas, tapas, platos, postre, cuenta.
Nunca presionas, siempre sugieres.
```

**Alexandra:**
```
Eres Alexandra, una barcelonesa que adora su ciudad.
No eres guía turística oficial, eres una amiga local.
Conoces los secretos, los rincones, los horarios reales.
Hablas como si estuvieras tomando un vermut con el usuario.
```

### Endpoints

| Camarero B2B | Alexandra B2C |
|--------------|---------------|
| `/api/tools/context` | `/api/tools/city_context` |
| `/api/tap` (NFC mesa) | `/api/session` (inicio sesión) |
| `/api/chat` | `/api/usage` (tracking costos) |
| - | `/api/upgrade` (Stripe) |

### Data Sources

| Camarero B2B | Alexandra B2C |
|--------------|---------------|
| `el_tigre.json` (menú) | `barcelona_places.json` |
| Precios, alérgenos | Ubicaciones, horarios |
| Historia del local | Historia de la ciudad |

---

## 8. Repositorios Git (Recomendado)

### Opción A: Dos repos separados

```
github.com/user/camarero-b2b     # Congelado
github.com/user/alexandra-tours  # Desarrollo activo
```

### Opción B: Monorepo con branches

```
github.com/user/hustler-platform
├── main                    # Alexandra Tours (activo)
├── camarero-b2b           # Branch preservada
└── docs/BIFURCATION.md    # Este documento
```

**Recomendación:** Opción A (repos separados) para claridad mental.

---

## 9. Resumen

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  CAMARERO B2B          │  ALEXANDRA B2C                │
│  ─────────────         │  ────────────                 │
│  Estado: Congelado     │  Estado: Desarrollo activo    │
│  Path: Camarero-B2B\   │  Path: Restaurante red\       │
│  Target: Restaurantes  │  Target: Turistas             │
│  Modelo: Suscripción   │  Modelo: Freemium + Hold      │
│                                                         │
│  NO MEZCLAR. Código y docs completamente separados.    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```
