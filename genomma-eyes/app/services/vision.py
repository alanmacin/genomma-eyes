"""
Servicio de análisis de imagen con Claude Vision.
Recibe una URL de imagen y devuelve inteligencia estructurada de punto de venta.
"""

from typing import Optional, Tuple
import json
import httpx
import base64
import anthropic
from app.config import settings
from app.models.schemas import VisionAnalysis

VISION_PROMPT = """Eres el agente de inteligencia de punto de venta de Genomma Lab.

Analiza esta foto y extrae en JSON:

1. tipo_tienda: super / farmacia / conveniencia / tradicional / otro
2. marcas_genomma: [{marca, producto, nivel_anaquel, stock_visible}]
3. competencia: [{marca, producto, observacion}]
4. alertas: [{tipo, descripcion}]
   tipos: quiebre_stock / precio_incorrecto / innovacion_competencia / mal_exhibido / producto_pirata
5. material_pop: {presente: bool, marca: str}
6. insight_principal: string de una línea

Responde SOLO JSON, sin texto adicional."""


async def download_image(url: str, twilio_auth: Optional[Tuple[str, str]] = None) -> Tuple[str, str]:
    """Descarga imagen y retorna (base64_data, media_type)."""
    async with httpx.AsyncClient() as client:
        if twilio_auth:
            response = await client.get(url, auth=twilio_auth, follow_redirects=True)
        else:
            response = await client.get(url, follow_redirects=True)
        response.raise_for_status()

        content_type = response.headers.get("content-type", "image/jpeg")
        media_type = content_type.split(";")[0].strip()
        image_b64 = base64.standard_b64encode(response.content).decode("utf-8")
        return image_b64, media_type


async def analyze_image(image_url: str, twilio_auth: Optional[Tuple[str, str]] = None) -> VisionAnalysis:
    """Analiza una imagen de punto de venta con Claude Vision."""
    image_b64, media_type = await download_image(image_url, twilio_auth)

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": VISION_PROMPT,
                    },
                ],
            }
        ],
    )

    raw_text = message.content[0].text

    # Limpiar posible markdown fence
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

    analysis_dict = json.loads(cleaned)
    return VisionAnalysis(**analysis_dict)
