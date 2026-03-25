from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel


class BrandDetection(BaseModel):
    marca: str
    producto: str
    nivel_anaquel: Optional[str] = None
    stock_visible: Optional[str] = None


class CompetitorDetection(BaseModel):
    marca: str
    producto: str
    observacion: Optional[str] = None


class Alert(BaseModel):
    tipo: str
    descripcion: str


class MaterialPOP(BaseModel):
    presente: bool
    marca: Optional[str] = None


class VisionAnalysis(BaseModel):
    tipo_tienda: str
    marcas_genomma: List[BrandDetection] = []
    competencia: List[CompetitorDetection] = []
    alertas: List[Alert] = []
    material_pop: Optional[MaterialPOP] = None
    insight_principal: str = ""
