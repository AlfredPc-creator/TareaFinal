from fastapi import APIRouter, HTTPException, Query, status
from bson import ObjectId
from pymongo.errors import DuplicateKeyError
from datetime import datetime, date
import re

from database import users_collection
from schemas.user import UserCreate, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


def to_mongo_datetime(value):
    """
    MongoDB no puede guardar datetime.date directamente.
    Convertimos date -> datetime (00:00:00).
    """
    if isinstance(value, date) and not isinstance(value, datetime):
        return datetime(value.year, value.month, value.day)
    return value


def serialize_user(user: dict) -> dict:
    
    fn = user.get("fecha_nacimiento")
    if isinstance(fn, datetime):
        fn_out = fn.date().isoformat()
    else:
        fn_out = str(fn)

    return {
        "id": str(user["_id"]),
        "nombre": user["nombre"],
        "apellidos": user["apellidos"],
        "dni": user["dni"],
        "fecha_nacimiento": fn_out,
        "created": user["created"],
        "updated": user["updated"],
    }


def validate_object_id(user_id: str) -> ObjectId:
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="ID inválido (ObjectId)")
    return ObjectId(user_id)


@router.get("", status_code=200)
def get_users():
    users = list(users_collection.find())
    return [serialize_user(u) for u in users]


@router.get("/{user_id}", status_code=200)
def get_user_by_id(user_id: str):
    _id = validate_object_id(user_id)
    user = users_collection.find_one({"_id": _id})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return serialize_user(user)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_user(user: UserCreate):
    data = user.model_dump()

   
    now = datetime.utcnow()
    data["created"] = now
    data["updated"] = now

    
    data["fecha_nacimiento"] = to_mongo_datetime(data["fecha_nacimiento"])

    try:
        result = users_collection.insert_one(data)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="El DNI ya existe (debe ser único)")

    new_user = users_collection.find_one({"_id": result.inserted_id})
    return serialize_user(new_user)


@router.patch("/{user_id}", status_code=200)
def update_user(user_id: str, user: UserUpdate):
    _id = validate_object_id(user_id)

    updates = {k: v for k, v in user.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No hay campos para actualizar")

   
    if "fecha_nacimiento" in updates:
        updates["fecha_nacimiento"] = to_mongo_datetime(updates["fecha_nacimiento"])

    updates["updated"] = datetime.utcnow()

    try:
        result = users_collection.update_one({"_id": _id}, {"$set": updates})
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="El DNI ya existe (debe ser único)")

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    user_updated = users_collection.find_one({"_id": _id})
    return serialize_user(user_updated)


@router.delete("/{user_id}", status_code=200)
def delete_user(user_id: str):
    _id = validate_object_id(user_id)
    result = users_collection.delete_one({"_id": _id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"message": "Usuario eliminado correctamente"}


@router.get("/search-by-dni/{dni}", status_code=200)
def search_by_dni(dni: str):
    user = users_collection.find_one({"dni": dni})
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return serialize_user(user)


@router.get("/search-by-nombre-apellido", status_code=200)
def search_by_nombre_apellido(
    nombre: str = Query(..., min_length=1),
    apellidos: str = Query(..., min_length=1),
):
   
    nombre_re = re.compile(re.escape(nombre), re.IGNORECASE)
    apellidos_re = re.compile(re.escape(apellidos), re.IGNORECASE)

    users = list(
        users_collection.find(
            {"nombre": {"$regex": nombre_re}, "apellidos": {"$regex": apellidos_re}}
        )
    )
    return [serialize_user(u) for u in users]