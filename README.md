# Aura Fitness API

Servidor para conectar Google Fitness (Fitbit) con Aura vía iOS Shortcuts.

## Endpoints

- `GET /` — Comprueba que el servidor funciona
- `GET /auth` — Inicia autenticación con Google
- `GET /callback` — Callback OAuth (automático)
- `GET /sleep` — Datos de sueño de anoche
- `GET /heart` — Frecuencia cardíaca en reposo
- `GET /summary` — Resumen completo de salud

## Variables de entorno en Render

| Variable | Valor |
|---|---|
| `GOOGLE_CLIENT_ID` | Tu Client ID de Google Cloud |
| `GOOGLE_CLIENT_SECRET` | Tu Client Secret de Google Cloud |

## Uso desde iOS Shortcuts

Llama a `https://aura-fitbit.onrender.com/summary` con una petición GET
y pasa el JSON resultante a Claude API para el briefing matutino.
