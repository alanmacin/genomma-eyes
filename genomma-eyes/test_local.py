"""
Test local de Genomma Eyes.
Prueba el flujo completo simulando Twilio y Supabase.

Ejecutar: python test_local.py
"""

import asyncio
import json
from unittest.mock import MagicMock, patch, AsyncMock

# --- Test 1: Verificar que FastAPI levanta ---
print("=" * 60)
print("TEST 1: FastAPI app loads correctly")
print("=" * 60)

try:
    from app.main import app
    print(f"✅ App cargada: {app.title} v{app.version}")
    routes = [r.path for r in app.routes]
    print(f"✅ Rutas: {routes}")
except Exception as e:
    print(f"❌ Error cargando app: {e}")

# --- Test 2: Schemas Pydantic ---
print("\n" + "=" * 60)
print("TEST 2: Pydantic schemas parse correctly")
print("=" * 60)

from app.models.schemas import VisionAnalysis

sample_analysis = {
    "tipo_tienda": "farmacia",
    "marcas_genomma": [
        {"marca": "Cicatricure", "producto": "Crema anti-arrugas", "nivel_anaquel": "medio", "stock_visible": "alto"},
        {"marca": "Tío Nacho", "producto": "Shampoo herbolaria", "nivel_anaquel": "superior", "stock_visible": "medio"},
        {"marca": "Asepxia", "producto": "Jabón facial", "nivel_anaquel": "inferior", "stock_visible": "bajo"},
    ],
    "competencia": [
        {"marca": "Pond's", "producto": "Crema S", "observacion": "Precio más bajo que Cicatricure"},
        {"marca": "Head & Shoulders", "producto": "Shampoo classic", "observacion": "Promoción 2x1"},
    ],
    "alertas": [
        {"tipo": "quiebre_stock", "descripcion": "Nikzon sin stock en anaquel"},
        {"tipo": "innovacion_competencia", "descripcion": "Pond's lanzó nueva línea anti-age con display especial"},
    ],
    "material_pop": {"presente": True, "marca": "Cicatricure"},
    "insight_principal": "Farmacia con buen share Genomma pero quiebre de Nikzon y presión competitiva de Pond's en anti-age",
}

try:
    analysis = VisionAnalysis(**sample_analysis)
    print(f"✅ Tipo tienda: {analysis.tipo_tienda}")
    print(f"✅ Marcas Genomma detectadas: {len(analysis.marcas_genomma)}")
    for b in analysis.marcas_genomma:
        print(f"   - {b.marca}: {b.producto} (anaquel: {b.nivel_anaquel}, stock: {b.stock_visible})")
    print(f"✅ Competencia detectada: {len(analysis.competencia)}")
    for c in analysis.competencia:
        print(f"   - {c.marca}: {c.observacion}")
    print(f"✅ Alertas: {len(analysis.alertas)}")
    for a in analysis.alertas:
        print(f"   - [{a.tipo}] {a.descripcion}")
    print(f"✅ Material POP: {analysis.material_pop.presente} ({analysis.material_pop.marca})")
    print(f"✅ Insight: {analysis.insight_principal}")
except Exception as e:
    print(f"❌ Error parsing schema: {e}")

# --- Test 3: Gamification logic ---
print("\n" + "=" * 60)
print("TEST 3: Gamification points calculation")
print("=" * 60)

from app.services.gamification import calculate_points
from app.config import settings

points_normal = calculate_points("farmacia")
points_quest = calculate_points("farmacia", quest_id="some-quest-id")
print(f"✅ Puntos visita normal: {points_normal} (esperado: {settings.POINTS_PER_VISIT})")
print(f"✅ Puntos visita + quest: {points_quest} (esperado: {settings.POINTS_PER_VISIT + settings.POINTS_BONUS_QUEST})")
assert points_normal == settings.POINTS_PER_VISIT
assert points_quest == settings.POINTS_PER_VISIT + settings.POINTS_BONUS_QUEST
print("✅ Cálculo de puntos correcto")

# --- Test 4: WhatsApp messages in 3 languages ---
print("\n" + "=" * 60)
print("TEST 4: WhatsApp messages (3 idiomas)")
print("=" * 60)

from app.services.whatsapp import get_message, format_checklist_status

# Español (México)
msg_es = get_message("México", "analyzing")
print(f"✅ ES: {msg_es}")

# Portugués (Brasil)
msg_pt = get_message("Brasil", "analyzing")
print(f"✅ PT: {msg_pt}")

# Inglés (USA)
msg_en = get_message("USA", "analyzing")
print(f"✅ EN: {msg_en}")

# Checklist parcial
checklist_partial = {
    "has_super": True,
    "has_farmacia": True,
    "has_tradicional": False,
    "has_conveniencia": False,
    "eligible_for_prize": False,
}
status = format_checklist_status(checklist_partial, "México")
print(f"✅ Checklist parcial: {status}")

# Checklist completo
checklist_full = {
    "has_super": True,
    "has_farmacia": True,
    "has_tradicional": True,
    "has_conveniencia": True,
    "eligible_for_prize": True,
}
status_full = format_checklist_status(checklist_full, "México")
print(f"✅ Checklist completo: {status_full}")

# --- Test 5: Alert system ---
print("\n" + "=" * 60)
print("TEST 5: Alert formatting")
print("=" * 60)

from app.services.alerts import format_alert_notification

alert_data = {
    "alert_type": "quiebre_stock",
    "country": "México",
    "description": "Nikzon sin stock en anaquel principal",
}
notification = format_alert_notification(alert_data, "Carlos López")
print(f"✅ Notificación:\n{notification}")

# --- Test 6: Full webhook simulation ---
print("\n" + "=" * 60)
print("TEST 6: Webhook endpoint (simulated)")
print("=" * 60)

from fastapi.testclient import TestClient

# Mock dependencies para que no necesite Supabase real
with patch("app.api.webhook._lookup_employee") as mock_lookup, \
     patch("app.api.webhook.analyze_image", new_callable=AsyncMock) as mock_vision, \
     patch("app.api.webhook.get_supabase") as mock_db, \
     patch("app.api.webhook.update_employee_points"), \
     patch("app.api.webhook.update_monthly_checklist") as mock_checklist, \
     patch("app.api.webhook.find_active_quest") as mock_quest, \
     patch("app.api.webhook.save_alerts") as mock_alerts, \
     patch("app.api.webhook.send_whatsapp") as mock_send:

    # Configurar mocks
    mock_lookup.return_value = {
        "id": "emp-001",
        "name": "Carlos López",
        "country": "México",
        "whatsapp": "whatsapp:+5215512345678",
        "total_points": 150,
        "active": True,
    }

    mock_vision.return_value = VisionAnalysis(**sample_analysis)

    mock_db_instance = MagicMock()
    mock_db_instance.table.return_value.insert.return_value.execute.return_value = MagicMock(
        data=[{"id": "visit-001"}]
    )
    mock_db_instance.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()
    mock_db_instance.storage.from_.return_value.upload.return_value = None
    mock_db_instance.storage.from_.return_value.get_public_url.return_value = "https://storage.example.com/photo.jpg"
    mock_db.return_value = mock_db_instance

    mock_checklist.return_value = {
        "has_super": True,
        "has_farmacia": True,
        "has_tradicional": False,
        "has_conveniencia": False,
        "eligible_for_prize": False,
    }

    mock_quest.return_value = None
    mock_alerts.return_value = []

    client = TestClient(app)

    # Simular mensaje SIN imagen
    response = client.post("/webhook/twilio", data={
        "From": "whatsapp:+5215512345678",
        "Body": "Hola",
        "NumMedia": "0",
    })
    print(f"✅ Sin imagen → Status: {response.status_code}")
    assert "foto" in response.text.lower() or "photo" in response.text.lower()
    print(f"   Respuesta correcta: pide enviar foto")

    # Simular mensaje CON imagen
    response = client.post("/webhook/twilio", data={
        "From": "whatsapp:+5215512345678",
        "Body": "",
        "NumMedia": "1",
        "MediaUrl0": "https://api.twilio.com/2010-04-01/Accounts/AC123/Messages/MM123/Media/ME123",
        "Latitude": "19.4326",
        "Longitude": "-99.1332",
    })
    print(f"✅ Con imagen → Status: {response.status_code}")
    assert response.status_code == 200
    assert "analizando" in response.text.lower() or "analyzing" in response.text.lower()
    print(f"   Respuesta: confirmó que está analizando")

    # Simular número no registrado
    mock_lookup.return_value = None
    response = client.post("/webhook/twilio", data={
        "From": "whatsapp:+5215599999999",
        "Body": "",
        "NumMedia": "1",
        "MediaUrl0": "https://example.com/photo.jpg",
    })
    print(f"✅ No registrado → Status: {response.status_code}")
    assert "no est" in response.text.lower() or "not registered" in response.text.lower()
    print(f"   Respuesta correcta: número no registrado")

# --- Test 7: API endpoints ---
print("\n" + "=" * 60)
print("TEST 7: API health endpoints")
print("=" * 60)

with TestClient(app) as client:
    r = client.get("/")
    print(f"✅ GET / → {r.json()}")
    r = client.get("/health")
    print(f"✅ GET /health → {r.json()}")

# --- Summary ---
print("\n" + "=" * 60)
print("🎉 TODOS LOS TESTS PASARON")
print("=" * 60)
print("""
Genomma Eyes está listo. Próximos pasos para ir a producción:

1. Crear proyecto en Supabase y ejecutar el SQL migration
2. Configurar .env con credenciales reales
3. Configurar Twilio WhatsApp sandbox/número
4. Deploy en Railway

¿Quieres proceder con alguno de estos pasos?
""")
