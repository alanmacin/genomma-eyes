"""
Webhook principal de Twilio WhatsApp.
Recibe fotos de empleados, analiza con Claude Vision, guarda en Supabase.
"""

from typing import Optional
import logging
from fastapi import APIRouter, Form, BackgroundTasks
from twilio.twiml.messaging_response import MessagingResponse

from app.config import settings
from app.services.vision import analyze_image
from app.services.gamification import (
    calculate_points,
    update_employee_points,
    update_monthly_checklist,
    find_active_quest,
)
from app.services.alerts import save_alerts
from app.services.whatsapp import (
    send_whatsapp,
    get_message,
    format_checklist_status,
)
from app.utils.supabase_client import get_supabase

logger = logging.getLogger(__name__)

router = APIRouter()


def _lookup_employee(whatsapp_number: str) -> Optional[dict]:
    """Busca empleado por número de WhatsApp."""
    db = get_supabase()
    result = (
        db.table("employees")
        .select("*")
        .eq("whatsapp", whatsapp_number)
        .eq("active", True)
        .execute()
    )
    return result.data[0] if result.data else None


def _upload_photo_to_storage(image_url: str, visit_id: str) -> str:
    """Sube la foto al storage de Supabase y retorna URL pública."""
    import httpx

    # Descargar imagen de Twilio
    response = httpx.get(
        image_url,
        auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
        follow_redirects=True,
    )
    response.raise_for_status()

    content_type = response.headers.get("content-type", "image/jpeg")
    ext = "jpg" if "jpeg" in content_type else content_type.split("/")[-1]
    file_path = f"visits/{visit_id}.{ext}"

    db = get_supabase()
    db.storage.from_("visit-photos").upload(
        file_path,
        response.content,
        {"content-type": content_type},
    )

    public_url = db.storage.from_("visit-photos").get_public_url(file_path)
    return public_url


async def _process_visit(
    employee: dict,
    image_url: str,
    lat: Optional[float],
    lng: Optional[float],
    whatsapp_from: str,
):
    """Procesa una visita completa en background."""
    db = get_supabase()
    country = employee["country"]

    try:
        # 1. Analizar imagen con Claude Vision
        twilio_auth = (settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        analysis = await analyze_image(image_url, twilio_auth)

        # 2. Buscar quest activa
        detected_brands = [b.marca for b in analysis.marcas_genomma]
        quest = None
        quest_id = None
        for brand in detected_brands:
            quest = find_active_quest(country, brand)
            if quest:
                quest_id = quest["id"]
                break

        # 3. Calcular puntos
        points = calculate_points(analysis.tipo_tienda, quest_id)

        # 4. Crear registro de visita
        visit_data = {
            "employee_id": employee["id"],
            "photo_url": image_url,  # URL temporal de Twilio por ahora
            "lat": lat,
            "lng": lng,
            "country": country,
            "store_type": analysis.tipo_tienda,
            "ai_analysis": analysis.model_dump(),
            "points_earned": points,
            "quest_id": quest_id,
        }
        visit_result = db.table("visits").insert(visit_data).execute()
        visit_id = visit_result.data[0]["id"]

        # 5. Subir foto a storage (reemplazar URL temporal)
        try:
            public_url = _upload_photo_to_storage(image_url, visit_id)
            db.table("visits").update({"photo_url": public_url}).eq("id", visit_id).execute()
        except Exception as e:
            logger.warning(f"No se pudo subir foto al storage: {e}")

        # 6. Actualizar puntos del empleado
        update_employee_points(employee["id"], points)
        new_total = (employee.get("total_points") or 0) + points

        # 7. Actualizar checklist mensual
        checklist = update_monthly_checklist(employee["id"], analysis.tipo_tienda)
        checklist_text = format_checklist_status(checklist, country)

        # 8. Guardar alertas
        critical_alerts = save_alerts(
            visit_id, employee["id"], country, analysis.alertas
        )

        # 9. Responder al empleado
        response_msg = get_message(
            country,
            "result",
            store_type=analysis.tipo_tienda,
            brands_count=len(analysis.marcas_genomma),
            competitors_count=len(analysis.competencia),
            insight=analysis.insight_principal,
            points=points,
            total_points=new_total,
            checklist_status=checklist_text,
        )

        # Agregar info de quest si aplica
        if quest:
            response_msg += "\n" + get_message(
                country,
                "quest_bonus",
                bonus=settings.POINTS_BONUS_QUEST,
                quest_title=quest["title"],
            )

        # Agregar info de alertas si hay
        if critical_alerts:
            response_msg += "\n" + get_message(
                country, "alert_found", count=len(critical_alerts)
            )

        send_whatsapp(whatsapp_from, response_msg)

    except Exception as e:
        logger.error(f"Error procesando visita: {e}", exc_info=True)
        send_whatsapp(whatsapp_from, get_message(country, "error"))


@router.post("/webhook/twilio")
async def twilio_webhook(
    background_tasks: BackgroundTasks,
    From: str = Form(...),
    Body: str = Form(default=""),
    NumMedia: str = Form(default="0"),
    MediaUrl0: str = Form(default=None),
    Latitude: str = Form(default=None),
    Longitude: str = Form(default=None),
):
    """
    Endpoint principal que recibe mensajes de WhatsApp via Twilio.
    """
    response = MessagingResponse()

    # Buscar empleado
    employee = _lookup_employee(From)
    if not employee:
        response.message(get_message("México", "not_registered"))
        return str(response)

    country = employee["country"]

    # Verificar que haya imagen
    if int(NumMedia) == 0 or not MediaUrl0:
        response.message(get_message(country, "no_image"))
        return str(response)

    # Parsear ubicación
    lat = float(Latitude) if Latitude else None
    lng = float(Longitude) if Longitude else None

    # Responder inmediatamente que estamos procesando
    response.message(get_message(country, "analyzing"))

    # Procesar en background
    background_tasks.add_task(
        _process_visit,
        employee,
        MediaUrl0,
        lat,
        lng,
        From,
    )

    return str(response)
