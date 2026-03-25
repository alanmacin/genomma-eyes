"""
Sistema de alertas críticas.
Cuando se detecta una alerta en el análisis de visión, se guarda y notifica.
"""

from app.utils.supabase_client import get_supabase
from app.models.schemas import Alert

CRITICAL_ALERT_TYPES = {"quiebre_stock", "producto_pirata", "precio_incorrecto"}


def save_alerts(
    visit_id: str,
    employee_id: str,
    country: str,
    alerts: list[Alert],
) -> list[dict]:
    """Guarda alertas en la base de datos y retorna las críticas."""
    if not alerts:
        return []

    db = get_supabase()
    critical = []

    for alert in alerts:
        alert_data = {
            "visit_id": visit_id,
            "employee_id": employee_id,
            "alert_type": alert.tipo,
            "description": alert.descripcion,
            "country": country,
            "resolved": False,
        }
        db.table("alerts").insert(alert_data).execute()

        if alert.tipo in CRITICAL_ALERT_TYPES:
            critical.append(alert_data)

    return critical


def format_alert_notification(alert: dict, employee_name: str) -> str:
    """Formatea una alerta para notificación por WhatsApp."""
    emoji_map = {
        "quiebre_stock": "🚨",
        "producto_pirata": "⚠️",
        "precio_incorrecto": "💰",
        "innovacion_competencia": "🔍",
        "mal_exhibido": "📦",
    }
    emoji = emoji_map.get(alert["alert_type"], "⚡")

    return (
        f"{emoji} *ALERTA: {alert['alert_type'].upper().replace('_', ' ')}*\n"
        f"📍 País: {alert['country']}\n"
        f"👤 Reportó: {employee_name}\n"
        f"📝 {alert['description']}"
    )
