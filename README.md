# Hustler IA - Camarero Inteligente (MVP Phase 1)

Sistema web NFC para restaurantes con IA contextual.

## Requisitos
- Python 3.10+ (Probado con **Python 3.11 ARM64**)
- Google Chrome (para probar la web)
- Dependencias (ver `requirements.txt`)

## Notas para Windows ARM64 (Surface Pro X / Mac Parallels)
Este proyecto ha sido optimizado para funcionar en arquitectura ARM64.
- Se ha sustituido **ChromaDB** por un sistema de RAG en memoria para evitar errores de compilación de librerías nativas (`pulsar-client`).
- Se recomienda usar el launcher `py -3.11` si tienes múltiples versiones de Python.

## Instalación

1.  Instalar dependencias:
    ```powershell
    # Si usas el launcher de Python:
    py -3.11 -m pip install -r backend/requirements.txt
    
    # O si tienes python en el PATH:
    python -m pip install -r backend/requirements.txt
    ```

2.  Configurar variables de entorno:
    - Renombrar `config/.env.example` a `config/.env`
    - (Opcional) Añadir API Keys reales si se desea probar con APIs externas.

## Ejecución

1.  Iniciar el servidor Backend:
    ```powershell
    # Desde la carpeta raíz (c:/Proyectos/Restaurante red)
    py -3.11 -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
    ```
    El servidor correrá en `http://127.0.0.1:8000`.

2.  Probar el flujo:
    - Abrir navegador en `http://127.0.0.1:8000/`.
    - Verás el Onboarding -> Chat.
    - Escribir en el chat para recibir respuesta simulada (RAG local).

## Tests
Hay un script de integración incluido para verificar seguridad y endpoints:
```powershell
py -3.11 test_integration.py
```
Este script verifica:
- Endpoint `/tap`
- Endpoint `/chat`
- Sanitización de XSS
- Headers CSP

## Seguridad Implementada
- **Versiones fijas**: Dependencias battle-tested.
- **Rate Limiting**: 5-10 req/min por IP.
- **Sanitización**: Input validation estricto con Pydantic.
- **CSP**: Headers de Content-Security-Policy en frontend.
