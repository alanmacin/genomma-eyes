"""
Motor de gamificación: puntos, checklist mensual, quests.
"""

from typing import Optional, List, Dict
from datetime import datetime, timezone
from app.config import settings
from app.utils.supabase_client import get_supabase

STORE_TYPE_FIELD_MAP = {
    "super": "has_super",
    "farmacia": "has_farmacia",
    "tradicional": "has_tradicional",
    "conveniencia": "has_conveniencia",
}


def calculate_points(store_type: str, quest_id: Optional[str] = None) -> int:
    """Calcula puntos ganados por una visita."""
    points = settings.POINTS_PER_VISIT
    if quest_id:
        points += settings.POINTS_BONUS_QUEST
    return points


def update_employee_points(employee_id: str, points: int) -> None:
    """Suma puntos al total del empleado."""
    db = get_supabase()
    employee = db.table("employees").select("total_points").eq("id", employee_id).single().execute()
    new_total = (employee.data.get("total_points") or 0) + points
    db.table("employees").update({"total_points": new_total}).eq("id", employee_id).execute()


def update_monthly_checklist(employee_id: str, store_type: str) -> dict:
    """
    Actualiza el checklist mensual del empleado.
    Retorna el estado actualizado del checklist.
    """
    db = get_supabase()
    current_month = datetime.now(timezone.utc).strftime("%Y-%m")

    # Buscar o crear checklist del mes
    result = (
        db.table("monthly_checklist")
        .select("*")
        .eq("employee_id", employee_id)
        .eq("month", current_month)
        .execute()
    )

    if not result.data:
        # Crear checklist nuevo
        checklist_data = {
            "employee_id": employee_id,
            "month": current_month,
            "has_super": False,
            "has_farmacia": False,
            "has_tradicional": False,
            "has_conveniencia": False,
            "eligible_for_prize": False,
        }
        db.table("monthly_checklist").insert(checklist_data).execute()
        checklist = checklist_data
    else:
        checklist = result.data[0]

    # Actualizar campo correspondiente al tipo de tienda
    field = STORE_TYPE_FIELD_MAP.get(store_type)
    if field and not checklist.get(field):
        update_data = {field: True}

        # Verificar si con esta visita se completan las 4
        updated_checklist = {**checklist, **update_data}
        all_complete = all(
            updated_checklist.get(f) for f in STORE_TYPE_FIELD_MAP.values()
        )
        if all_complete:
            update_data["eligible_for_prize"] = True
            # Bonus por completar las 4 categorías
            update_employee_points(employee_id, settings.POINTS_BONUS_COMPLETE_CHECKLIST)

        db.table("monthly_checklist").update(update_data).eq(
            "employee_id", employee_id
        ).eq("month", current_month).execute()

        checklist.update(update_data)

    return checklist


def find_active_quest(country: str, target_brand: Optional[str] = None) -> Optional[dict]:
    """Busca quest activa para el país y marca."""
    db = get_supabase()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    query = (
        db.table("quests")
        .select("*")
        .eq("active", True)
        .lte("start_date", today)
        .gte("end_date", today)
        .contains("countries", [country])
    )

    result = query.execute()

    if not result.data:
        return None

    # Si hay marca detectada, buscar quest que coincida
    if target_brand:
        for quest in result.data:
            if quest.get("target_brand", "").lower() in target_brand.lower():
                return quest

    return result.data[0]


def get_leaderboard(country: Optional[str] = None, limit: int = 10) -> List[dict]:
    """Obtiene ranking de empleados."""
    db = get_supabase()
    query = db.table("employees").select("id, name, country, total_points, area").eq("active", True)

    if country:
        query = query.eq("country", country)

    result = query.order("total_points", desc=True).limit(limit).execute()
    return result.data or []
