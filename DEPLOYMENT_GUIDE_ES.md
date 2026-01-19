# 🚀 Despliegue en Producción 24/7

Para tener a Alexandra disponible 24/7 sin tu ordenador encendido, necesitamos subir el código a la nube. Está preparado para plataformas modernas y gratuitas.

## 1. Preparación (GitHub)

1.  Crea una cuenta en [GitHub.com](https://github.com) si no tienes.
2.  Crea un **Nuevo Repositorio** (ponle nombre `alexandra-voice`).
3.  Sube tu código actual a ese repositorio.
    *   Puedes usar GitHub Desktop o la terminal si tienes git instalado.
    *   Asegúrate de subir la carpeta `backend` y `frontend` y el archivo `Procfile`.

## 2. Desplegar Backend (Cerebro) 🧠

Usaremos **Render** (o Railway) que tienen capa gratuita para Python.

1.  Ve a [render.com](https://render.com) y crea una cuenta.
2.  Pulsa **"New +"** y selecciona **"Web Service"**.
3.  Conecta tu cuenta de GitHub y selecciona el repositorio `alexandra-voice`.
4.  Render detectará casi todo automáticamente:
    *   **Name**: `alexandra-api` (o lo que quieras).
    *   **Region**: Frankfurt (mejor latencia para España) o New York.
    *   **Runtime**: Python 3.
    *   **Build Command**: `pip install -r backend/requirements.txt`
    *   **Start Command**: `uvicorn backend.main_v2:app --host 0.0.0.0 --port $PORT` (Render debería leer esto del `Procfile` automáticamente).
5.  Pulsa **"Create Web Service"**.
6.  Espera unos minutos. Te dará una URL pública HTTPS eterna:
    *   Ejemplo: `https://alexandra-api.onrender.com`
    *   ⚠️ **IMPORTANTE**: Ve a tu panel de ElevenLabs > Agents y actualiza la URL de las Tools para usar esta nueva dirección en vez de ngrok.

## 3. Desplegar Frontend (Cara) 🎨

Usaremos **Netlify** (el más fácil, drag & drop).

1.  Ve a [netlify.com](https://netlify.com) e inicia sesión.
2.  Ve a la pestaña "Sites".
3.  Arrastra la carpeta `frontend` de tu ordenador y suéltala en el navegador.
4.  ¡Listo! Te dará una URL (ej. `alexandra-demo.netlify.app`).

### Configurar Dominio Propio (Opcional)
Si tienes `bareltigre.com` y quieres que `voice.bareltigre.com` sea la app:

1.  En Netlify > Site Settings > Domain Management.
2.  Añade tu dominio `voice.bareltigre.com`.
3.  Netlify te dirá que crees un registro **CNAME** en tu proveedor de dominio (GoDaddy, Namecheap, etc.) apuntando a la URL de Netlify.

---

## Resumen de Arquitectura Final

*   **Usuario (Móvil)** 📱 ➡️ entra en `voice.bareltigre.com` (Netlify).
*   **Voz** 🎙️ ➡️ viaja directo a **ElevenLabs** (Latency cero).
*   **Datos/Menú** 📋 ➡️ ElevenLabs llama a `alexandra-api.onrender.com`.
*   **Tu PC** 💻 ➡️ **APAGADO** 😴. Todo funciona solo.
