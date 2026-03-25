"""
Servicio de mensajería WhatsApp via Twilio.
"""

from typing import Optional
from twilio.rest import Client
from app.config import settings

_twilio_client: Optional[Client] = None


def get_twilio_client() -> Client:
    global _twilio_client
    if _twilio_client is None:
        _twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    return _twilio_client


def send_whatsapp(to: str, body: str) -> None:
    """Envía mensaje de WhatsApp."""
    client = get_twilio_client()
    client.messages.create(
        from_=settings.TWILIO_WHATSAPP_NUMBER,
        to=to,
        body=body,
    )


MESSAGES = {
    "es": {
        "welcome": "👋 ¡Hola {name}! Soy *Genomma Eyes* 👁️\nEnvíame una foto de punto de venta y te doy puntos.",
        "analyzing": "📸 Recibí tu foto. Analizando...",
        "result": (
            "✅ *Visita registrada*\n\n"
            "🏪 Tipo: {store_type}\n"
            "🏷️ Marcas Genomma: {brands_count}\n"
            "🔍 Competencia: {competitors_count}\n"
            "💡 Insight: {insight}\n\n"
            "⭐ *+{points} puntos* (Total: {total_points})\n\n"
            "{checklist_status}"
        ),
        "checklist_complete": "🎉 ¡Completaste las 4 categorías del mes! Ya estás en el ranking de premios.",
        "checklist_pending": "📋 Checklist: {status}",
        "quest_bonus": "🎯 *¡QUEST COMPLETADA!* +{bonus} puntos extra\nMisión: {quest_title}",
        "alert_found": "⚠️ Se detectaron {count} alerta(s). El equipo fue notificado.",
        "not_registered": "❌ Tu número no está registrado. Contacta a tu supervisor.",
        "no_image": "📷 Envíame una *foto* de punto de venta para registrar tu visita.",
        "error": "😅 Hubo un error procesando tu imagen. Intenta de nuevo.",
    },
    "pt": {
        "welcome": "👋 Olá {name}! Eu sou *Genomma Eyes* 👁️\nEnvie uma foto do ponto de venda e ganhe pontos.",
        "analyzing": "📸 Recebi sua foto. Analisando...",
        "result": (
            "✅ *Visita registrada*\n\n"
            "🏪 Tipo: {store_type}\n"
            "🏷️ Marcas Genomma: {brands_count}\n"
            "🔍 Concorrência: {competitors_count}\n"
            "💡 Insight: {insight}\n\n"
            "⭐ *+{points} pontos* (Total: {total_points})\n\n"
            "{checklist_status}"
        ),
        "checklist_complete": "🎉 Você completou as 4 categorias do mês! Já está no ranking de prêmios.",
        "checklist_pending": "📋 Checklist: {status}",
        "quest_bonus": "🎯 *QUEST COMPLETADA!* +{bonus} pontos extra\nMissão: {quest_title}",
        "alert_found": "⚠️ {count} alerta(s) detectada(s). A equipe foi notificada.",
        "not_registered": "❌ Seu número não está registrado. Entre em contato com seu supervisor.",
        "no_image": "📷 Envie uma *foto* do ponto de venda para registrar sua visita.",
        "error": "😅 Houve um erro ao processar sua imagem. Tente novamente.",
    },
    "en": {
        "welcome": "👋 Hi {name}! I'm *Genomma Eyes* 👁️\nSend me a store photo and earn points.",
        "analyzing": "📸 Got your photo. Analyzing...",
        "result": (
            "✅ *Visit registered*\n\n"
            "🏪 Type: {store_type}\n"
            "🏷️ Genomma brands: {brands_count}\n"
            "🔍 Competition: {competitors_count}\n"
            "💡 Insight: {insight}\n\n"
            "⭐ *+{points} points* (Total: {total_points})\n\n"
            "{checklist_status}"
        ),
        "checklist_complete": "🎉 You completed all 4 store categories this month! You're in the prize ranking.",
        "checklist_pending": "📋 Checklist: {status}",
        "quest_bonus": "🎯 *QUEST COMPLETED!* +{bonus} extra points\nMission: {quest_title}",
        "alert_found": "⚠️ {count} alert(s) detected. The team has been notified.",
        "not_registered": "❌ Your number is not registered. Contact your supervisor.",
        "no_image": "📷 Send me a *photo* of the store to register your visit.",
        "error": "😅 There was an error processing your image. Please try again.",
    },
}

COUNTRY_LANG = {
    "Brasil": "pt",
    "USA": "en",
}


def get_lang(country: str) -> str:
    return COUNTRY_LANG.get(country, "es")


def get_message(country: str, key: str, **kwargs) -> str:
    lang = get_lang(country)
    template = MESSAGES[lang][key]
    return template.format(**kwargs) if kwargs else template


def format_checklist_status(checklist: dict, country: str) -> str:
    lang = get_lang(country)
    checks = {
        "super": "🛒" if checklist.get("has_super") else "⬜",
        "farmacia": "💊" if checklist.get("has_farmacia") else "⬜",
        "tradicional": "🏪" if checklist.get("has_tradicional") else "⬜",
        "conveniencia": "🏬" if checklist.get("has_conveniencia") else "⬜",
    }

    if checklist.get("eligible_for_prize"):
        return get_message(country, "checklist_complete")

    status = " ".join(f"{emoji}{name}" for name, emoji in checks.items())
    return get_message(country, "checklist_pending", status=status)
