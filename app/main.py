from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from . import models, schemas
from .database import Base, engine, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="ERP – Inventarios (Unidades y Zonas) • v1")

# -------------------------------
# Root
# -------------------------------
@app.get("/")
def home():
    return {
        "mensaje": "Inventarios | Propiedad privada y Zonas comunes",
        "docs": "/docs",
        "version": "v1"
    }

# -------------------------------
# SEED de catálogos (para probar rápido)
# -------------------------------
@app.post("/api/v1/catalogos/seed", tags=["Catálogos"])
def seed_catalogos(db: Session = Depends(get_db)):
    # Estados por defecto
    estados = [
        {"nombre": "Bueno", "orden_severidad": 1},
        {"nombre": "Requiere mantenimiento", "orden_severidad": 3},
        {"nombre": "No operativo", "orden_severidad": 4},
    ]
    for e in estados:
        if not db.query(models.CatalogoEstado).filter_by(nombre=e["nombre"]).first():
            db.add(models.CatalogoEstado(**e))

    # Categorías por defecto
    categorias = [
        {"nombre": "Ambiente", "descripcion": "Ambiente físico (cocina, baño, etc.)"},
        {"nombre": "Implemento", "descripcion": "Insumos o implementos"},
        {"nombre": "Mobiliario", "descripcion": "Muebles/equipos"},
    ]
    for c in categorias:
        if not db.query(models.CatalogoCategoria).filter_by(nombre=c["nombre"]).first():
            db.add(models.CatalogoCategoria(**c))

    db.commit()
    return {"ok": True, "detalle": "Catálogos cargados (idempotente)."}

@app.get("/api/v1/catalogos/estados", response_model=List[schemas.CatalogoEstadoOut], tags=["Catálogos"])
def listar_estados(db: Session = Depends(get_db)):
    return db.query(models.CatalogoEstado).order_by(models.CatalogoEstado.orden_severidad.asc()).all()

@app.get("/api/v1/catalogos/categorias", response_model=List[schemas.CatalogoCategoriaOut], tags=["Catálogos"])
def listar_categorias(db: Session = Depends(get_db)):
    return db.query(models.CatalogoCategoria).order_by(models.CatalogoCategoria.nombre.asc()).all()

# -------------------------------
# ARTÍCULOS (ejemplo)
# -------------------------------
@app.get("/api/v1/articulos", response_model=List[schemas.Articulo], tags=["Artículos"])
def leer_articulos(db: Session = Depends(get_db)):
    return db.query(models.Articulo).all()

@app.get("/api/v1/articulos/{articulo_id}", response_model=schemas.Articulo, tags=["Artículos"])
def leer_articulo(articulo_id: int, db: Session = Depends(get_db)):
    articulo = db.query(models.Articulo).filter(models.Articulo.id == articulo_id).first()
    if not articulo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artículo no encontrado")
    return articulo

@app.post("/api/v1/articulos", response_model=schemas.Articulo, status_code=status.HTTP_201_CREATED, tags=["Artículos"])
def crear_articulo(payload: schemas.ArticuloCreate, db: Session = Depends(get_db)):
    db_articulo = models.Articulo(**payload.model_dump())
    db.add(db_articulo)
    db.commit()
    db.refresh(db_articulo)
    return db_articulo

@app.put("/api/v1/articulos/{articulo_id}", response_model=schemas.Articulo, tags=["Artículos"])
def actualizar_articulo(articulo_id: int, payload: schemas.ArticuloCreate, db: Session = Depends(get_db)):
    db_articulo = db.query(models.Articulo).filter(models.Articulo.id == articulo_id).first()
    if not db_articulo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artículo no encontrado")
    for k, v in payload.model_dump().items():
        setattr(db_articulo, k, v)
    db.commit()
    db.refresh(db_articulo)
    return db_articulo

@app.delete("/api/v1/articulos/{articulo_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Artículos"])
def eliminar_articulo(articulo_id: int, db: Session = Depends(get_db)):
    db_articulo = db.query(models.Articulo).filter(models.Articulo.id == articulo_id).first()
    if not db_articulo:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Artículo no encontrado")
    db.delete(db_articulo)
    db.commit()
    return None

# -------------------------
# UNIDADES (propiedad privada)
# -------------------------
@app.post("/api/v1/unidades", response_model=schemas.UnidadOut, status_code=status.HTTP_201_CREATED, tags=["Unidades"])
def crear_unidad(payload: schemas.UnidadCreate, db: Session = Depends(get_db)):
    unidad = models.Unidad(**payload.model_dump())
    db.add(unidad)
    db.commit()
    db.refresh(unidad)
    return unidad

@app.get("/api/v1/unidades", response_model=List[schemas.UnidadOut], tags=["Unidades"])
def listar_unidades(
    torre: Optional[str] = None,
    piso: Optional[int] = None,
    db: Session = Depends(get_db)
):
    q = db.query(models.Unidad)
    if torre:
        q = q.filter(models.Unidad.torre == torre)
    if piso is not None:
        q = q.filter(models.Unidad.piso == piso)
    return q.all()

@app.get("/api/v1/unidades/{unidad_id}", response_model=schemas.UnidadOut, tags=["Unidades"])
def obtener_unidad(unidad_id: int, db: Session = Depends(get_db)):
    u = db.query(models.Unidad).filter(models.Unidad.id == unidad_id).first()
    if not u:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidad no encontrada")
    return u

@app.post("/api/v1/unidades/{unidad_id}/items", response_model=schemas.UnidadItemOut, status_code=status.HTTP_201_CREATED, tags=["Unidades"])
def agregar_item_unidad(unidad_id: int, payload: schemas.UnidadItemCreate, db: Session = Depends(get_db)):
    u = db.query(models.Unidad).filter(models.Unidad.id == unidad_id).first()
    if not u:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidad no encontrada")
    item = models.UnidadItem(unidad_id=unidad_id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@app.get("/api/v1/unidades/{unidad_id}/items", response_model=List[schemas.UnidadItemOut], tags=["Unidades"])
def listar_items_unidad(unidad_id: int, db: Session = Depends(get_db)):
    u = db.query(models.Unidad).filter(models.Unidad.id == unidad_id).first()
    if not u:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unidad no encontrada")
    return u.items

# -------------------------
# ZONAS COMUNES
# -------------------------
@app.post("/api/v1/zonas", response_model=schemas.ZonaOut, status_code=status.HTTP_201_CREATED, tags=["Zonas"])
def crear_zona(payload: schemas.ZonaCreate, db: Session = Depends(get_db)):
    z = models.ZonaComun(**payload.model_dump())
    db.add(z)
    db.commit()
    db.refresh(z)
    return z

@app.get("/api/v1/zonas", response_model=List[schemas.ZonaOut], tags=["Zonas"])
def listar_zonas(
    tipo: Optional[str] = None,
    db: Session = Depends(get_db)
):
    q = db.query(models.ZonaComun)
    if tipo:
        q = q.filter(models.ZonaComun.tipo == tipo)
    return q.all()

@app.get("/api/v1/zonas/{zona_id}", response_model=schemas.ZonaOut, tags=["Zonas"])
def obtener_zona(zona_id: int, db: Session = Depends(get_db)):
    z = db.query(models.ZonaComun).filter(models.ZonaComun.id == zona_id).first()
    if not z:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zona no encontrada")
    return z

@app.post("/api/v1/zonas/{zona_id}/items", response_model=schemas.ZonaItemOut, status_code=status.HTTP_201_CREATED, tags=["Zonas"])
def agregar_item_zona(zona_id: int, payload: schemas.ZonaItemCreate, db: Session = Depends(get_db)):
    z = db.query(models.ZonaComun).filter(models.ZonaComun.id == zona_id).first()
    if not z:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zona no encontrada")
    item = models.ZonaItem(zona_id=zona_id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@app.get("/api/v1/zonas/{zona_id}/items", response_model=List[schemas.ZonaItemOut], tags=["Zonas"])
def listar_items_zona(zona_id: int, db: Session = Depends(get_db)):
    z = db.query(models.ZonaComun).filter(models.ZonaComun.id == zona_id).first()
    if not z:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zona no encontrada")
    return z.items

# -------------------------
# CHECKLISTS
# -------------------------
@app.post("/api/v1/checklists", response_model=schemas.ChecklistOut, status_code=status.HTTP_201_CREATED, tags=["Checklists"])
def crear_checklist(payload: schemas.ChecklistCreate, db: Session = Depends(get_db)):
    ch = models.Checklist(**payload.model_dump())
    db.add(ch)
    db.commit()
    db.refresh(ch)
    return ch

@app.post("/api/v1/checklists/{checklist_id}/items", response_model=schemas.ChecklistItemOut, status_code=status.HTTP_201_CREATED, tags=["Checklists"])
def agregar_item_checklist(checklist_id: int, payload: schemas.ChecklistItemCreate, db: Session = Depends(get_db)):
    ch = db.query(models.Checklist).filter(models.Checklist.id == checklist_id).first()
    if not ch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checklist no encontrado")
    it = models.ChecklistItem(checklist_id=checklist_id, **payload.model_dump())
    db.add(it)
    db.commit()
    db.refresh(it)
    return it

# -------------------------
# INSPECCIONES
# -------------------------
@app.post("/api/v1/inspecciones", response_model=schemas.InspeccionOut, status_code=status.HTTP_201_CREATED, tags=["Inspecciones"])
def crear_inspeccion(payload: schemas.InspeccionCreate, db: Session = Depends(get_db)):
    # Validar que exista solo unidad o zona (no ambos, no ninguno)
    if bool(payload.unidad_id) == bool(payload.zona_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="La inspección debe referir a UNA unidad O UNA zona.")
    ch = db.query(models.Checklist).filter(models.Checklist.id == payload.checklist_id).first()
    if not ch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checklist no encontrado")
    ins = models.Inspeccion(
        fecha=payload.fecha,
        inspector=payload.inspector,
        checklist_id=payload.checklist_id,
        unidad_id=payload.unidad_id,
        zona_id=payload.zona_id
    )
    db.add(ins)
    db.commit()
    db.refresh(ins)
    return ins

@app.post("/api/v1/inspecciones/{inspeccion_id}/detalles", response_model=schemas.InspeccionDetalleOut, status_code=status.HTTP_201_CREATED, tags=["Inspecciones"])
def agregar_detalle_inspeccion(inspeccion_id: int, payload: schemas.InspeccionDetalleCreate, db: Session = Depends(get_db)):
    ins = db.query(models.Inspeccion).filter(models.Inspeccion.id == inspeccion_id).first()
    if not ins:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspección no encontrada")
    # Validar coherencia: detalle debe apuntar a item de la misma unidad/zona
    if bool(payload.unidad_item_id) == bool(payload.zona_item_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El detalle debe referir a UN item de UNIDAD o de ZONA.")
    if payload.unidad_item_id:
        ui = db.query(models.UnidadItem).filter(models.UnidadItem.id == payload.unidad_item_id).first()
        if not ui or ins.unidad_id != ui.unidad_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El item de unidad no corresponde a la inspección.")
    if payload.zona_item_id:
        zi = db.query(models.ZonaItem).filter(models.ZonaItem.id == payload.zona_item_id).first()
        if not zi or ins.zona_id != zi.zona_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El item de zona no corresponde a la inspección.")

    # Validar estado existente
    est = db.query(models.CatalogoEstado).filter(models.CatalogoEstado.id == payload.estado_id).first()
    if not est:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Estado inválido")

    det = models.InspeccionDetalle(
        inspeccion_id=inspeccion_id,
        unidad_item_id=payload.unidad_item_id,
        zona_item_id=payload.zona_item_id,
        estado_id=payload.estado_id,
        observacion=payload.observacion
    )
    db.add(det)
    db.commit()
    db.refresh(det)
    return det

@app.get("/api/v1/inspecciones/{inspeccion_id}", tags=["Inspecciones"])
def obtener_inspeccion(inspeccion_id: int, db: Session = Depends(get_db)):
    ins = db.query(models.Inspeccion).filter(models.Inspeccion.id == inspeccion_id).first()
    if not ins:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inspección no encontrada")
    # Devolver con detalles:
    detalles = db.query(models.InspeccionDetalle).filter(models.InspeccionDetalle.inspeccion_id == inspeccion_id).all()
    return {
        "inspeccion": schemas.InspeccionOut.model_validate(ins).model_dump(),
        "detalles": [schemas.InspeccionDetalleOut.model_validate(d).model_dump() for d in detalles]
    }

# -------------------------
# PENDIENTES (simple: todo lo que NO está 'Bueno')
# -------------------------
@app.get("/api/v1/pendientes", tags=["Reportes"])
def listar_pendientes(db: Session = Depends(get_db)):
    # Estados cuyo nombre != "Bueno"
    estados_no_ok = db.query(models.CatalogoEstado.id).filter(models.CatalogoEstado.nombre != "Bueno").subquery()
    detalles = db.query(models.InspeccionDetalle).filter(models.InspeccionDetalle.estado_id.in_(estados_no_ok)).all()
    salida = []
    for d in detalles:
        ref = {}
        if d.unidad_item:
            ref = {
                "ambito": "UNIDAD",
                "unidad_id": d.unidad_item.unidad_id,
                "unidad_item_id": d.unidad_item.id,
                "item_nombre": d.unidad_item.nombre
            }
        elif d.zona_item:
            ref = {
                "ambito": "ZONA",
                "zona_id": d.zona_item.zona_id,
                "zona_item_id": d.zona_item.id,
                "item_nombre": d.zona_item.nombre
            }
        salida.append({
            "inspeccion_id": d.inspeccion_id,
            "estado_id": d.estado_id,
            "observacion": d.observacion,
            **ref
        })
    return {"total": len(salida), "pendientes": salida}
