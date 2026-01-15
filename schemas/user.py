from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime


class UserBase(BaseModel):
    nombre: str = Field(..., min_length=1)
    apellidos: str = Field(..., min_length=1)
    dni: str = Field(..., min_length=8, max_length=15)
    fecha_nacimiento: date


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
 
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    dni: Optional[str] = None
    fecha_nacimiento: Optional[date] = None


class UserOut(UserBase):
    id: str
    created: datetime
    updated: datetime
