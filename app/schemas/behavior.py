"""Formatos de comportamientos. (REQ 4, 5)"""
from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

class BehaviorOut(BaseModel):
    """Para el listado (REQ 4)."""
    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )
    id: int
    name: str
    is_default: bool


class BehaviorDetailOut(BehaviorOut):
    """Para el detalle (REQ 5). TODO: agregar lo que corresponda (reglas que sigue, parámetros, etc.)."""
    code: str