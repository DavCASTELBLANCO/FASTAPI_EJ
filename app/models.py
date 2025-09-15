from sqlalchemy import (
    Column, Integer, String, ForeignKey, DateTime, Boolean, Text, Enum, UniqueConstraint
)
from sqlalchemy.types import JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .database import Base

# -------------------------
# ARTICULOS (ejemplo que ya tenías)
# -------------------------
class Articulo(Base):
    __tablename__ = "articulos"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    precio = Column(Integer, nullable=False)

# -------------------------
# CATALOGOS
# -------------------------
class CatalogoEstado(Base):
    __tablename__ = "catalogo_estado"
    id = Column(Integer, primary_key=True)
    nombre = Column(String, unique=True, nullable=False)  # "Bueno", "Requiere mantenimiento", "No operativo"
    orden_severidad = Column(Integer, nullable=False, default=1)  # 1=OK, 2=Observación, 3=Falla

class CatalogoCategoria(Base):
    __tablename__ = "catalogo_categoria"
    id = Column(Integer, primary_key=True)
    nombre = Column(String, unique=True, nullable=False)  # "Ambiente", "Implemento", "Mobiliario"
    descripcion = Column(String, nullable=True)

# -------------------------
# PROPIEDAD PRIVADA (UNIDAD) y ZONAS COMUNES
# -------------------------
class Unidad(Base):
    __tablename__ = "unidades"
    id = Column(Integer, primary_key=True, index=True)
    torre = Column(String, nullable=False)
    piso = Column(Integer, nullable=False)
    numero = Column(String, nullable=False)

    __table_args__ = (UniqueConstraint("torre", "piso", "numero", name="uq_unidad_ref"),)

    items = relationship("UnidadItem", back_populates="unidad", cascade="all, delete-orphan")

class UnidadItem(Base):
    __tablename__ = "unidad_items"
    id = Column(Integer, primary_key=True)
    unidad_id = Column(Integer, ForeignKey("unidades.id", ondelete="CASCADE"), nullable=False, index=True)
    nombre = Column(String, nullable=False)  # "Cocina", "Baño", "Kit limpieza"
    categoria_id = Column(Integer, ForeignKey("catalogo_categoria.id"), nullable=True)
    estado_id = Column(Integer, ForeignKey("catalogo_estado.id"), nullable=True)
    observacion = Column(String, nullable=True)

    unidad = relationship("Unidad", back_populates="items")
    categoria = relationship("CatalogoCategoria")
    estado = relationship("CatalogoEstado")

class ZonaComun(Base):
    __tablename__ = "zonas_comunes"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)     # "Terraza BBQ", "Sala de juegos"
    ubicacion = Column(String, nullable=True)   # "Piso 15"
    tipo = Column(String, nullable=True)        # "Recreación", "Servicios"
    items = relationship("ZonaItem", back_populates="zona", cascade="all, delete-orphan")

class ZonaItem(Base):
    __tablename__ = "zona_items"
    id = Column(Integer, primary_key=True)
    zona_id = Column(Integer, ForeignKey("zonas_comunes.id", ondelete="CASCADE"), nullable=False, index=True)
    nombre = Column(String, nullable=False)     # "BBQ", "Caneca", "Futbolito"
    categoria_id = Column(Integer, ForeignKey("catalogo_categoria.id"), nullable=True)
    estado_id = Column(Integer, ForeignKey("catalogo_estado.id"), nullable=True)
    observacion = Column(String, nullable=True)

    zona = relationship("ZonaComun", back_populates="items")
    categoria = relationship("CatalogoCategoria")
    estado = relationship("CatalogoEstado")

# -------------------------
# CHECKLISTS e INSPECCIONES
# -------------------------
class AmbitoEnum(str, enum.Enum):
    UNIDAD = "UNIDAD"
    ZONA = "ZONA"

class TipoRespuestaEnum(str, enum.Enum):
    SI_NO = "SI_NO"
    OPCIONES = "OPCIONES"
    NUMERICO = "NUMERICO"
    TEXTO = "TEXTO"

class Checklist(Base):
    __tablename__ = "checklists"
    id = Column(Integer, primary_key=True)
    nombre = Column(String, nullable=False)
    version = Column(String, nullable=False, default="1.0")
    ambito = Column(Enum(AmbitoEnum), nullable=False)

    items = relationship("ChecklistItem", back_populates="checklist", cascade="all, delete-orphan")

class ChecklistItem(Base):
    __tablename__ = "checklist_items"
    id = Column(Integer, primary_key=True)
    checklist_id = Column(Integer, ForeignKey("checklists.id", ondelete="CASCADE"), nullable=False)
    texto = Column(String, nullable=False)  # p.ej., "Lavaplatos sin fugas"
    tipo_respuesta = Column(Enum(TipoRespuestaEnum), nullable=False, default=TipoRespuestaEnum.SI_NO)
    opciones = Column(String, nullable=True)  # CSV para opciones si aplica

    checklist = relationship("Checklist", back_populates="items")

class Inspeccion(Base):
    __tablename__ = "inspecciones"
    id = Column(Integer, primary_key=True)
    fecha = Column(DateTime, default=datetime.utcnow, nullable=False)
    inspector = Column(String, nullable=False)
    checklist_id = Column(Integer, ForeignKey("checklists.id"), nullable=False)

    # Polimorfismo simple: una inspección es sobre UNA unidad O UNA zona
    unidad_id = Column(Integer, ForeignKey("unidades.id"), nullable=True)
    zona_id = Column(Integer, ForeignKey("zonas_comunes.id"), nullable=True)

    checklist = relationship("Checklist")
    detalles = relationship("InspeccionDetalle", back_populates="inspeccion", cascade="all, delete-orphan")

class InspeccionDetalle(Base):
    __tablename__ = "inspeccion_detalles"
    id = Column(Integer, primary_key=True)
    inspeccion_id = Column(Integer, ForeignKey("inspecciones.id", ondelete="CASCADE"), nullable=False)
    # El detalle refiere a UN item de UNIDAD o de ZONA (no ambos)
    unidad_item_id = Column(Integer, ForeignKey("unidad_items.id"), nullable=True)
    zona_item_id = Column(Integer, ForeignKey("zona_items.id"), nullable=True)

    estado_id = Column(Integer, ForeignKey("catalogo_estado.id"), nullable=False)  # resultado observado
    observacion = Column(Text, nullable=True)
    valor_json = Column(JSON, nullable=True)  # si quieres guardar respuesta compleja

    inspeccion = relationship("Inspeccion", back_populates="detalles")
    estado = relationship("CatalogoEstado")
    unidad_item = relationship("UnidadItem")
    zona_item = relationship("ZonaItem")
