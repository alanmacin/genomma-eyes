# 👁️ Genomma Eyes

Plataforma de inteligencia colectiva de punto de venta para Genomma Lab Internacional.

Empleados envían fotos de tiendas por WhatsApp → IA analiza → inteligencia de mercado en tiempo real.

## Arquitectura

```
WhatsApp → Twilio → FastAPI Webhook → Claude Vision → Supabase
                                                        ↓
                                              Streamlit Dashboard
```

## Setup rápido

### 1. Clonar y dependencias

```bash
cd "Agente Eyes"
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Variables de entorno

```bash
cp .env.example .env
# Editar .env con tus credenciales
```

### 3. Base de datos

1. Crear proyecto en [Supabase](https://supabase.com)
2. Ir a SQL Editor
3. Copiar y ejecutar `migrations/001_initial_schema.sql`
4. Copiar URL y keys al `.env`

### 4. Twilio WhatsApp

1. Crear cuenta en [Twilio](https://twilio.com)
2. Activar WhatsApp Sandbox (o número aprobado)
3. Configurar webhook: `https://tu-app.railway.app/webhook/twilio` (POST)
4. Copiar credenciales al `.env`

### 5. Anthropic API

1. Obtener API key en [Anthropic Console](https://console.anthropic.com)
2. Agregarla al `.env`

### 6. Ejecutar

```bash
# Backend
uvicorn app.main:app --reload

# Dashboard (en otra terminal)
streamlit run dashboard/app.py
```

## Deploy en Railway

1. Conectar repo a Railway
2. Agregar variables de entorno
3. Railway usa el `Dockerfile` automáticamente
4. Para el dashboard, crear segundo servicio con:
   ```
   streamlit run dashboard/app.py --server.port $PORT --server.address 0.0.0.0
   ```

## Estructura

```
├── app/
│   ├── main.py              # FastAPI app
│   ├── config.py             # Variables de entorno
│   ├── api/
│   │   └── webhook.py        # Webhook Twilio WhatsApp
│   ├── services/
│   │   ├── vision.py         # Claude Vision analysis
│   │   ├── gamification.py   # Puntos, checklist, quests
│   │   ├── alerts.py         # Sistema de alertas
│   │   └── whatsapp.py       # Mensajería y templates
│   ├── models/
│   │   └── schemas.py        # Pydantic models
│   └── utils/
│       └── supabase_client.py
├── dashboard/
│   └── app.py                # Streamlit dashboard
├── migrations/
│   └── 001_initial_schema.sql
├── Dockerfile
├── railway.toml
└── requirements.txt
```

## Flujo completo

1. **Empleado** envía foto + ubicación por WhatsApp
2. **Twilio** recibe y envía al webhook `/webhook/twilio`
3. **Claude Vision** analiza: tipo tienda, marcas Genomma, competencia, alertas
4. **Supabase** guarda visita, foto, análisis JSON
5. **Gamificación** suma puntos, actualiza checklist mensual
6. **Alertas** críticas se guardan y notifican
7. **Dashboard** muestra todo en tiempo real

## Reglas de negocio

- 4 visitas mínimas/mes: 1 súper, 1 farmacia, 1 tradicional, 1 conveniencia
- Solo quien complete las 4 entra al ranking de premios
- Premios mensuales: $2,000 / $1,000 / $500 MXN (tarjetas Amazon)
- Gran Premio Anual: $100,000 - $200,000 MXN
- Quests: misiones especiales con premio extra

## Países

México, USA, Brasil, Argentina, Colombia, Chile, Perú, Ecuador, Guatemala, Honduras, El Salvador, Costa Rica, Nicaragua, Panamá, Bolivia, Paraguay, Rep. Dominicana.

Bot responde en español, portugués o inglés según el país del empleado.
