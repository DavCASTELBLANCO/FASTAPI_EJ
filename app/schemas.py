from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Literal
from datetime import datetime
from .models import AmbitoEnum, TipoRespuestaEnum

# Config Pydantic v2
class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

# -------------------------
# ARTICULOS (ejemplo)
# -------------------------
class ArticuloBase(ORMModel):
    nombre: str
    precio: int

class ArticuloCreate(ArticuloBase):
    pass

class Articulo(ArticuloBase):
    id: int

# -------------------------
# CATALOGOS
# -------------------------
class CatalogoEstadoCreate(ORMModel):
    nombre: str
    orden_severidad: int = 1

class CatalogoEstadoOut(ORMModel):
    id: int
    nombre: str
    orden_severidad: int

class CatalogoCategoriaCreate(ORMModel):
    nombre: str
    descripcion: Optional[str] = None

class CatalogoCategoriaOut(ORMModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None

# -------------------------
# UNIDADES y ZONAS
# -------------------------
class UnidadItemBase(ORMModel):
    nombre: str
    categoria_id: Optional[int] = None
    estado_id: Optional[int] = None
    observacion: Optional[str] = None

class UnidadItemCreate(UnidadItemBase):
    pass

class UnidadItemOut(UnidadItemBase):
    id: int
    categoria_id: Optional[int] = None
    estado_id: Optional[int] = None

class UnidadBase(ORMModel):
    torre: str
    piso: int
    numero: str

class UnidadCreate(UnidadBase):
    pass

class UnidadOut(UnidadBase):
    id: int
    items: List[UnidadItemOut] = []

class ZonaItemBase(ORMModel):
    nombre: str
    categoria_id: Optional[int] = None
    estado_id: Optional[int] = None
    observacion: Optional[str] = None

class ZonaItemCreate(ZonaItemBase):
    pass

class ZonaItemOut(ZonaItemBase):
    id: int

class ZonaBase(ORMModel):
    nombre: str
    ubicacion: Optional[str] = None
    tipo: Optional[str] = None

class ZonaCreate(ZonaBase):
    pass

class ZonaOut(ZonaBase):
    id: int
    items: List[ZonaItemOut] = []

# -------------------------
# CHECKLISTS e INSPECCIONES
# -------------------------
class ChecklistItemCreate(ORMModel):
    texto: str
    tipo_respuesta: TipoRespuestaEnum = TipoRespuestaEnum.SI_NO
    opciones: Optional[str] = None  # CSV cuando es OPCIONES

class ChecklistItemOut(ChecklistItemCreate):
    id: int

class ChecklistCreate(ORMModel):
    nombre: str
    version: str = "1.0"
    ambito: AmbitoEnum

class ChecklistOut(ChecklistCreate):
    id: int
    items: List[ChecklistItemOut] = []

class InspeccionCreate(ORMModel):
    fecha: Optional[datetime] = None
    inspector: str
    checklist_id: int
    unidad_id: Optional[int] = None
    zona_id: Optional[int] = None

class InspeccionOut(InspeccionCreate):
    id: int

class InspeccionDetalleCreate(ORMModel):
    unidad_item_id: Optional[int] = None
    zona_item_id: Optional[int] = None
    estado_id: int
    observacion: Optional[str] = None

class InspeccionDetalleOut(InspeccionDetalleCreate):
    id: int
